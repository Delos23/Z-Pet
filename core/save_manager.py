import json
import os
from pathlib import Path
import time

import settings
from core.pet import Pet

SAVE_FILE: Path = settings.SAVE_DIR / "save.json"
CONFIG_FILE: Path = settings.SAVE_DIR / "config.json"

DEFAULT_CONFIG: dict = {
    "clock_24h": False,
    "sky_mode": "auto",    # "auto", "dawn", "day", "sunset", "night"
    "time_scale": 1.0,     # 1.0, 10.0, or 60.0
}


def _atomic_write_json(path: Path, payload: dict) -> None:
    settings.SAVE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = path.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_file, path)


def load_config() -> dict:
    """Loads user settings from ~/.config/z-pet/config.json with safe defaults."""
    cfg = dict(DEFAULT_CONFIG)
    if not CONFIG_FILE.exists():
        return cfg

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            cfg["clock_24h"] = bool(raw.get("clock_24h", cfg["clock_24h"]))
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
    """Peeks at saved pet info for the Start-Up screen without advancing offline time."""
    if not SAVE_FILE.exists():
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        born_at = float(data.get("born_at", time.time()))
        age_hours = max(0, int((time.time() - born_at) // 3600))
        return {
            "name": str(data.get("name", "SPARKKIT")),
            "age_hours": age_hours,
            "bond": int(data.get("bond", 0)),
            "alive": bool(data.get("alive", True)),
        }
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None


def save_pet(pet: Pet) -> None:
    """Atomically writes pet state to ~/.config/z-pet/save.json."""
    _atomic_write_json(SAVE_FILE, pet.to_dict())


def create_new_pet(name: str = "SPARKKIT") -> Pet:
    """Creates and saves a brand-new pet, replacing any previous save."""
    clean_name = name.strip().upper()[:10] or "SPARKKIT"
    pet = Pet({"name": clean_name})
    save_pet(pet)
    return pet


def load_pet(time_scale: float = 1.0) -> tuple[Pet, float]:
    """Loads saved pet and applies offline elapsed time. Returns (pet, offline_seconds)."""
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