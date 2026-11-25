import json
import os
from pathlib import Path

import settings
from core.pet import Pet

SAVE_FILE: Path = settings.SAVE_DIR / "save.json"


def save_pet(pet: Pet) -> None:
    """Atomically writes pet state to ~/.config/z-pet/save.json."""
    settings.SAVE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = SAVE_FILE.with_suffix(".tmp")

    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(pet.to_dict(), f, indent=2)

    # Atomic rename prevents corrupt saves if battery dies mid-write
    os.replace(tmp_file, SAVE_FILE)


def load_pet() -> tuple[Pet, float]:
    """Loads saved pet and applies offline elapsed time. Returns (pet, offline_seconds)."""
    if not SAVE_FILE.exists():
        pet = Pet()
        save_pet(pet)
        return pet, 0.0

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        pet = Pet(data)
        offline_seconds = pet.apply_offline_time()
        save_pet(pet)
        return pet, offline_seconds
    except (OSError, json.JSONDecodeError, ValueError):
        # Fallback cleanly if a save file was manually broken
        pet = Pet()
        save_pet(pet)
        return pet, 0.0