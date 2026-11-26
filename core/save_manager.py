import json
import os
from pathlib import Path
import time

import settings
from core.pet import Pet
from core.species import get_species

SAVE_FILE: Path = settings.SAVE_DIR / "save.json"
CONFIG_FILE: Path = settings.SAVE_DIR / "config.json"
GUIDE_FILE: Path = settings.SAVE_DIR / "guide.json"

DEFAULT_CONFIG: dict = {
    "clock_24h": False,
    "sky_mode": "auto",
    "time_scale": 1.0,
    "sound": True,
}

_DISCOVERED_CACHE: set[str] | None = None


def _atomic_write_json(path: Path, payload: dict) -> None:
    settings.SAVE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = path.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_file, path)


def load_discovered_species() -> set[str]:
    """Loads permanently discovered species IDs for The Guide."""
    global _DISCOVERED_CACHE
    if _DISCOVERED_CACHE is not None:
        return set(_DISCOVERED_CACHE)

    discovered: set[str] = set()
    if GUIDE_FILE.exists():
        try:
            with open(GUIDE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict) and isinstance(raw.get("discovered"), list):
                discovered = {str(sid) for sid in raw["discovered"]}
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            pass

    _DISCOVERED_CACHE = discovered
    return set(discovered)


def record_discovery(species_id: str) -> bool:
    """Marks a species as discovered in guide.json. Returns True if newly unlocked."""
    global _DISCOVERED_CACHE
    if not species_id:
        return False
    discovered = load_discovered_species()
    if species_id in discovered:
        return False

    discovered.add(species_id)
    _DISCOVERED_CACHE = discovered
    _atomic_write_json(GUIDE_FILE, {"discovered": sorted(discovered)})
    return True


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if not CONFIG_FILE.exists():
        return cfg

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            cfg["clock_24h"] = bool(raw.get("clock_24h", cfg["clock_24h"]))
            cfg["sound"] = bool(raw.get("sound", cfg["sound"]))
            sky = str(raw.get("sky_mode", cfg["sky_mode"]))
            if sky in ("auto", "dawn", "day", "sunset", "night"):
                cfg["sky_mode"] = sky
            scale = float(raw.get("time_scale", cfg["time_scale"]))
            if scale in (1.0, 10.0, 60.0):
                cfg["time_scale"] = scale
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    _atomic_write_json(CONFIG_FILE, cfg)


def has_save() -> bool:
    return SAVE_FILE.exists()


def get_save_preview() -> dict | None:
    if not SAVE_FILE.exists():
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        born_at = float(data.get("born_at", time.time()))
        age_hours = max(0, int((time.time() - born_at) // 3600))
        species_id = str(data.get("species_id", "spark_kit"))
        return {
            "name": str(data.get("name", get_species(species_id)["default_name"])),
            "species_id": species_id,
            "color": str(data.get("color", "purple")),
            "level": int(data.get("level", 1)),
            "age_hours": age_hours,
            "bond": int(data.get("bond", 0)),
            "alive": bool(data.get("alive", True)),
        }
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None


def save_pet(pet: Pet) -> None:
    record_discovery(pet.species_id)
    _atomic_write_json(SAVE_FILE, pet.to_dict())


def create_new_pet(
    name: str = "",
    color: str = "purple",
    species_id: str = "spark_kit",
) -> Pet:
    """Creates and saves a brand-new starter pet; blank name keeps species default."""
    sp = get_species(species_id)
    clean_name = name.strip().upper()[:10] or sp["default_name"]
    pet = Pet({
        "name": clean_name,
        "species_id": species_id,
        "color": color,
        "stage": sp.get("stage", "baby"),
        "battle_stats": dict(sp["base_stats"]),
    })
    save_pet(pet)
    return pet


def load_pet(time_scale: float = 1.0) -> tuple[Pet, float]:
    if not SAVE_FILE.exists():
        pet = Pet()
        save_pet(pet)
        return pet, 0.0

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        pet = Pet(data)
        offline_seconds = pet.apply_offline_time(time_scale=time_scale)
        save_pet(pet)
        return pet, offline_seconds
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        pet = Pet()
        save_pet(pet)
        return pet, 0.0