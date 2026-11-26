"""Loads species metadata, personality modifiers, and 3-stage care-driven evolutions."""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "species.json"
_CACHE: dict | None = None

TEEN_EVOLVE_LEVEL = 10
ADULT_EVOLVE_LEVEL = 20

PERSONALITIES: dict[str, dict] = {
    "hyper": {
        "label": "Hyper",
        "desc": "+25% Play XP, faster walk, hungrier",
        "hunger_decay": 1.15,
        "happy_decay": 1.0,
        "energy_decay": 1.0,
        "clean_decay": 1.0,
        "sleep_mult": 1.0,
        "play_xp_mult": 1.25,
        "train_xp_mult": 1.0,
        "care_xp_mult": 1.0,
        "meal_bonus": 0.0,
        "hug_bond_bonus": 0,
        "perfect_stat_bonus": 0,
        "walk_speed_mult": 1.25,
    },
    "bold": {
        "label": "Bold",
        "desc": "+25% Train XP, hearty meals, tires fast",
        "hunger_decay": 1.0,
        "happy_decay": 1.0,
        "energy_decay": 1.10,
        "clean_decay": 1.0,
        "sleep_mult": 1.0,
        "play_xp_mult": 1.0,
        "train_xp_mult": 1.25,
        "care_xp_mult": 1.0,
        "meal_bonus": 4.0,
        "hug_bond_bonus": 0,
        "perfect_stat_bonus": 0,
        "walk_speed_mult": 1.05,
    },
    "serene": {
        "label": "Serene",
        "desc": "Slow fatigue, +20% sleep, messy fast",
        "hunger_decay": 1.0,
        "happy_decay": 0.95,
        "energy_decay": 0.80,
        "clean_decay": 1.10,
        "sleep_mult": 1.20,
        "play_xp_mult": 1.0,
        "train_xp_mult": 1.0,
        "care_xp_mult": 1.0,
        "meal_bonus": 0.0,
        "hug_bond_bonus": 0,
        "perfect_stat_bonus": 0,
        "walk_speed_mult": 0.90,
    },
    "gentle": {
        "label": "Gentle",
        "desc": "+1 Bond Hugs/Treats, slow hunger",
        "hunger_decay": 0.80,
        "happy_decay": 0.95,
        "energy_decay": 1.0,
        "clean_decay": 1.0,
        "sleep_mult": 1.0,
        "play_xp_mult": 1.0,
        "train_xp_mult": 1.0,
        "care_xp_mult": 1.0,
        "meal_bonus": 0.0,
        "hug_bond_bonus": 1,
        "perfect_stat_bonus": 0,
        "walk_speed_mult": 0.82,
    },
    "curious": {
        "label": "Curious",
        "desc": "+25% Care XP, +1 Perfect drill, needy",
        "hunger_decay": 1.0,
        "happy_decay": 1.15,
        "energy_decay": 1.0,
        "clean_decay": 1.0,
        "sleep_mult": 1.0,
        "play_xp_mult": 1.0,
        "train_xp_mult": 1.0,
        "care_xp_mult": 1.25,
        "meal_bonus": 0.0,
        "hug_bond_bonus": 0,
        "perfect_stat_bonus": 1,
        "walk_speed_mult": 1.12,
    },
}

CARE_PATH_META = {
    "radiant": ("Radiant", (105, 225, 145)),
    "trained": ("Trained", (110, 185, 245)),
    "wild":    ("Wild",    (245, 165, 95)),
}


def load_species_db() -> dict:
    global _CACHE
    if _CACHE is None:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _CACHE = json.load(f)
    return _CACHE


def get_species(species_id: str) -> dict:
    db = load_species_db()
    if species_id in db:
        return db[species_id]
    return db["spark_kit"]


def get_starter_ids() -> list[str]:
    db = load_species_db()
    return [sid for sid, info in db.items() if info.get("starter")]


def get_personality(species_id: str) -> dict:
    sp = get_species(species_id)
    pid = str(sp.get("personality", "hyper"))
    return PERSONALITIES.get(pid, PERSONALITIES["hyper"])


def get_next_evolve_level(stage: str) -> int | None:
    if stage == "baby":
        return TEEN_EVOLVE_LEVEL
    if stage == "teen":
        return ADULT_EVOLVE_LEVEL
    return None


def evaluate_care_path(pet, final_check: bool = False) -> str:
    """Determines Radiant, Trained, or Wild care path for Lv.10 (Teen) and Lv.20 (Adult)."""
    stage = str(getattr(pet, "stage", "baby"))
    mistakes = int(getattr(pet, "care_mistakes", 0))
    drills = int(getattr(pet, "training_sessions", 0))
    bond = int(getattr(pet, "bond", 0))

    if stage == "baby":
        # Baby -> Teen (Lv.10)
        if mistakes >= 3:
            return "wild"
        if final_check:
            if drills >= 4 and (drills * 7 >= bond or mistakes == 2):
                return "trained"
            if mistakes <= 1 and bond >= 20:
                return "radiant"
            if drills >= 3 and mistakes <= 2:
                return "trained"
            return "wild"
        if drills >= 3 and (drills * 7 >= max(1, bond) or mistakes == 2):
            return "trained"
        return "radiant" if mistakes <= 1 else "wild"

    # Teen -> Adult (Lv.20)
    if mistakes >= 5:
        return "wild"
    if final_check:
        if drills >= 9 and (drills * 6 >= bond or mistakes >= 2):
            return "trained"
        if mistakes <= 2 and bond >= 45:
            return "radiant"
        if drills >= 7 and mistakes <= 3:
            return "trained"
        return "wild"
    if drills >= 7 and (drills * 6 >= max(1, bond) or mistakes >= 2):
        return "trained"
    return "radiant" if mistakes <= 2 else "wild"


def find_evolution(pet) -> str | None:
    """Returns the target species_id when a Baby reaches Lv.10 or a Teen reaches Lv.20."""
    if not pet.alive:
        return None
    sp = get_species(pet.species_id)
    evolutions = sp.get("evolutions", {})
    if not isinstance(evolutions, dict) or not evolutions:
        return None

    req_level = get_next_evolve_level(pet.stage)
    if req_level is None or pet.level < req_level:
        return None

    path = evaluate_care_path(pet, final_check=True)
    return evolutions.get(path) or evolutions.get("wild")


def get_evolution_hint(pet) -> tuple[str, tuple]:
    """Returns (status_line, color) showing next Teen/Adult target and live Care Path."""
    sp = get_species(pet.species_id)
    evolutions = sp.get("evolutions", {})
    req_level = get_next_evolve_level(pet.stage)
    if not isinstance(evolutions, dict) or not evolutions or req_level is None:
        return ("Stage: Fully Evolved Adult", (255, 224, 96))

    path = evaluate_care_path(pet, final_check=(pet.level >= req_level))
    path_label, path_col = CARE_PATH_META.get(path, ("Radiant", (105, 225, 145)))
    target_id = evolutions.get(path)
    target_name = get_species(target_id)["name"] if target_id else "???"
    return (f"{path_label} -> {target_name} (Lv.{req_level})", path_col)