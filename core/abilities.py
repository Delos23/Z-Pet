"""Combat math, wild rival generator, and all 35 species ability definitions."""

import random

from core.animator import PET_COLOR_ORDER
from core.species import get_species, load_species_db

# Maps every ability.id in data/species.json to concrete battle behavior
ABILITY_EFFECTS: dict[str, dict] = {
    # --- 5 Baby Abilities ---
    "static_pounce":  {"stat": "atk", "power": 2.4, "priority": True},
    "ember_bite":     {"stat": "atk", "power": 2.7, "burn": 2},
    "bubble_jet":     {"stat": "int", "power": 2.7},
    "leaf_flurry":    {"stat": "int", "power": 2.3, "debuff_def": 0.20},
    "logic_ping":     {"stat": "int", "power": 2.4, "crit_bonus": 0.35},

    # --- 15 Teen Abilities ---
    "astral_gleam":   {"stat": "int", "power": 2.4, "buff_int": 0.22},
    "spark_dash":     {"stat": "atk", "power": 2.7, "priority": True},
    "static_swipe":   {"stat": "atk", "power": 2.9, "crit_bonus": 0.25},
    "warm_glow":      {"stat": "int", "power": 2.0, "heal_pct": 0.22},
    "flame_lunge":    {"stat": "atk", "power": 3.1},
    "smolder_snap":   {"stat": "atk", "power": 2.7, "low_hp_boost": True},
    "pearl_mist":     {"stat": "int", "power": 2.1, "buff_def": 0.25},
    "surge_fin":      {"stat": "int", "power": 3.0},
    "trench_bite":    {"stat": "atk", "power": 2.6, "drain": 0.35},
    "petal_breeze":   {"stat": "int", "power": 1.8, "heal_pct": 0.28},
    "timber_guard":   {"stat": "atk", "power": 2.0, "buff_def": 0.30, "shield": True},
    "briar_peck":     {"stat": "atk", "power": 2.5, "thorns": 2},
    "chime_pulse":    {"stat": "int", "power": 2.5, "buff_spd": 0.25},
    "target_lock":    {"stat": "hybrid", "power": 2.8, "pierce": True},
    "byte_jolt":      {"stat": "int", "power": 2.7, "crit_bonus": 0.35},

    # --- 15 Adult Abilities ---
    "star_shield":    {"stat": "int", "power": 2.4, "buff_def": 0.25, "reflect": True},
    "thunder_fang":   {"stat": "atk", "power": 3.1, "pierce": True, "priority": True},
    "wild_surge":     {"stat": "atk", "power": 2.9, "low_hp_boost": True},
    "solar_blessing": {"stat": "int", "power": 2.5, "heal_pct": 0.26},
    "blaze_rush":     {"stat": "atk", "power": 3.5},
    "cinder_grudge":  {"stat": "atk", "power": 2.8, "revenge": True},
    "tidal_aegis":    {"stat": "int", "power": 2.1, "heal_pct": 0.26, "buff_def": 0.28},
    "tempest_pulse":  {"stat": "int", "power": 3.4},
    "riptide_drain":  {"stat": "int", "power": 2.9, "drain": 0.45},
    "pollen_renewal": {"stat": "int", "power": 2.0, "heal_pct": 0.32, "bond_heal": True},
    "bastion_roar":   {"stat": "atk", "power": 2.4, "buff_def": 0.35, "reflect": True},
    "bramble_snare":  {"stat": "atk", "power": 2.8, "thorns": 3},
    "time_skip":      {"stat": "spd", "power": 1.8, "hits": 2},
    "overclock_beam": {"stat": "hybrid", "power": 3.4},
    "hex_scramble":   {"stat": "int", "power": 3.1, "debuff_def": 0.25, "crit_bonus": 0.25},
}


def calc_max_hp(level: int, def_stat: int) -> int:
    return 55 + level * 8 + int(def_stat) * 2


def get_ability_spec(species_id: str) -> tuple[str, str, str, dict]:
    """Returns (ability_id, name, desc, effect_dict) for any species."""
    sp = get_species(species_id)
    ab = sp.get("ability") or {"id": "static_pounce", "name": "Power Strike", "desc": "Focused strike"}
    ab_id = str(ab.get("id", "static_pounce"))
    effect = ABILITY_EFFECTS.get(ab_id, {"stat": "atk", "power": 2.6})
    return ab_id, str(ab["name"]), str(ab["desc"]), effect


def make_fighter_from_pet(pet) -> dict:
    """Builds a live battle state dictionary from the player's Pet."""
    ab_id, ab_name, ab_desc, ab_fx = get_ability_spec(pet.species_id)
    stats = {
        "atk": int(pet.battle_stats.get("atk", 8)),
        "def": int(pet.battle_stats.get("def", 6)),
        "spd": int(pet.battle_stats.get("spd", 8)),
        "int": int(pet.battle_stats.get("int", 6)),
    }
    max_hp = calc_max_hp(pet.level, stats["def"])
    return {
        "name": pet.name,
        "species_id": pet.species_id,
        "color": pet.color,
        "level": pet.level,
        "bond": pet.bond,
        "stats": stats,
        "max_hp": max_hp,
        "hp": max_hp,
        "sp": 1,
        "max_sp": 3,
        "ability_id": ab_id,
        "ability_name": ab_name,
        "ability_desc": ab_desc,
        "ability_fx": ab_fx,
        "guarding": False,
        "reflect": False,
        "def_mult": 1.0,
        "int_mult": 1.0,
        "spd_mult": 1.0,
        "dot_turns": 0,
        "dot_label": "",
        "took_hit_last": False,
    }


def spawn_wild_rival(player_level: int, exclude_species: str = "") -> dict:
    """Generates a level-appropriate wild Z-Pet opponent (Baby / Teen / Adult)."""
    db = load_species_db()
    rival_lvl = max(1, min(30, player_level + random.choice((-1, 0, 0, 1))))

    if rival_lvl < 10:
        stage = "baby"
    elif rival_lvl < 20:
        stage = "teen"
    else:
        stage = "adult"

    pool = [sid for sid, info in db.items() if info.get("stage") == stage]
    non_mirror = [sid for sid in pool if sid != exclude_species]
    species_id = random.choice(non_mirror or pool)
    sp = db[species_id]

    # Scale rival stats smoothly with level (slightly softer than a trained player pet)
    base = sp["base_stats"]
    growth = sp["growth"]
    stage_offset = 0 if stage == "baby" else (9 if stage == "teen" else 19)
    lvl_steps = max(0, rival_lvl - 1 - stage_offset)

    stats = {}
    for k in ("atk", "def", "spd", "int"):
        raw = base[k] + int(lvl_steps * growth[k] * 0.85) + (stage_offset * 1.15)
        stats[k] = max(5, min(145, int(raw * random.uniform(0.92, 1.05))))

    ab_id, ab_name, ab_desc, ab_fx = get_ability_spec(species_id)
    max_hp = calc_max_hp(rival_lvl, stats["def"])

    return {
        "name": sp["name"].upper(),
        "species_id": species_id,
        "color": random.choice(PET_COLOR_ORDER),
        "level": rival_lvl,
        "bond": 0,
        "stats": stats,
        "max_hp": max_hp,
        "hp": max_hp,
        "sp": 1,
        "max_sp": 3,
        "ability_id": ab_id,
        "ability_name": ab_name,
        "ability_desc": ab_desc,
        "ability_fx": ab_fx,
        "guarding": False,
        "reflect": False,
        "def_mult": 1.0,
        "int_mult": 1.0,
        "spd_mult": 1.0,
        "dot_turns": 0,
        "dot_label": "",
        "took_hit_last": False,
    }


def effective_stat(fighter: dict, key: str) -> float:
    base = float(fighter["stats"][key])
    if key == "def":
        return max(3.0, base * fighter["def_mult"])
    if key == "int":
        return max(3.0, base * fighter["int_mult"])
    if key == "spd":
        return max(3.0, base * fighter["spd_mult"])
    return base


def resolve_action(attacker: dict, defender: dict, action: str) -> dict:
    """Resolves 'strike', 'skill', or 'guard' and returns damage/heal/log events."""
    result = {
        "action": action,
        "damage": 0,
        "healed": 0,
        "reflected": 0,
        "crit": False,
        "dodged": False,
        "sp_refund": False,
        "message": "",
    }

    if action == "guard":
        attacker["guarding"] = True
        attacker["sp"] = min(attacker["max_sp"], attacker["sp"] + 1)
        heal_amt = max(3, int(attacker["max_hp"] * 0.08 + effective_stat(attacker, "def") * 0.08))
        actual_heal = min(attacker["max_hp"] - attacker["hp"], heal_amt)
        attacker["hp"] += actual_heal
        result["healed"] = actual_heal
        result["message"] = f"{attacker['name']} braced! (+{actual_heal} HP, +1 SP)"
        return result

    atk_spd = effective_stat(attacker, "spd")
    def_spd = effective_stat(defender, "spd")
    def_val = effective_stat(defender, "def")
    int_val = effective_stat(attacker, "int")

    is_skill = action == "skill"
    fx = attacker["ability_fx"] if is_skill else {"stat": "atk", "power": 2.0}

    if is_skill:
        attacker["sp"] = max(0, attacker["sp"] - 2)
    else:
        attacker["sp"] = min(attacker["max_sp"], attacker["sp"] + 1)

    # Dodge check (SPD advantage gives up to 18% evade; priority/pierce skills are harder to dodge)
    dodge_chance = max(0.0, (def_spd - atk_spd) * 0.004)
    dodge_chance = min(0.18, dodge_chance)
    if fx.get("priority") or fx.get("pierce"):
        dodge_chance *= 0.4

    if random.random() < dodge_chance:
        result["dodged"] = True
        move_name = attacker["ability_name"] if is_skill else "Strike"
        result["message"] = f"{defender['name']} dodged {move_name}!"
        return result

    # Choose offensive stat
    stat_kind = fx.get("stat", "atk")
    if stat_kind == "hybrid":
        off_val = (effective_stat(attacker, "atk") + int_val) * 0.62
    elif stat_kind == "int":
        off_val = int_val
    elif stat_kind == "spd":
        off_val = atk_spd
    else:
        off_val = effective_stat(attacker, "atk")

    power = float(fx.get("power", 2.0))
    if fx.get("low_hp_boost"):
        missing_ratio = 1.0 - (attacker["hp"] / max(1, attacker["max_hp"]))
        power *= 1.0 + missing_ratio * 0.55
    if fx.get("revenge") and attacker["took_hit_last"]:
        power *= 1.35

    # INT subtly amplifies all signature skills
    if is_skill:
        power *= 1.0 + min(0.35, int_val * 0.0025)

    pierce = bool(fx.get("pierce", False))
    eff_def = def_val * (0.45 if pierce else 1.0)
    mitigation = 60.0 / (60.0 + eff_def)

    crit_chance = 0.06 + max(0.0, (atk_spd - def_spd) * 0.006) + float(fx.get("crit_bonus", 0.0))
    crit_chance = min(0.48, crit_chance)

    hits = int(fx.get("hits", 1))
    total_dmg = 0
    for _ in range(hits):
        raw = off_val * power + attacker["level"] * 1.6
        dmg = raw * mitigation * random.uniform(0.92, 1.08)
        if random.random() < crit_chance:
            dmg *= 1.45
            result["crit"] = True
        if defender["guarding"]:
            dmg *= 0.50
        total_dmg += max(3, int(round(dmg)))

    defender["hp"] = max(0, defender["hp"] - total_dmg)
    defender["took_hit_last"] = True
    result["damage"] = total_dmg

    # Reflect shield check
    if defender["reflect"] and total_dmg > 0:
        ref_dmg = max(3, int(total_dmg * 0.30))
        attacker["hp"] = max(0, attacker["hp"] - ref_dmg)
        result["reflected"] = ref_dmg
        defender["reflect"] = False

    # Secondary skill effects (heals, lifesteal, buffs, debuffs, DoTs)
    if is_skill:
        if fx.get("drain"):
            heal_amt = max(2, int(total_dmg * float(fx["drain"])))
            actual = min(attacker["max_hp"] - attacker["hp"], heal_amt)
            attacker["hp"] += actual
            result["healed"] += actual

        if fx.get("heal_pct"):
            pct = float(fx["heal_pct"])
            bonus = (min(100, attacker["bond"]) * 0.0015) if fx.get("bond_heal") else 0.0
            heal_amt = max(5, int(attacker["max_hp"] * (pct + bonus) + int_val * 0.15))
            actual = min(attacker["max_hp"] - attacker["hp"], heal_amt)
            attacker["hp"] += actual
            result["healed"] += actual

        if fx.get("buff_def"):
            attacker["def_mult"] = min(1.75, attacker["def_mult"] + float(fx["buff_def"]))
        if fx.get("buff_int"):
            attacker["int_mult"] = min(1.75, attacker["int_mult"] + float(fx["buff_int"]))
        if fx.get("buff_spd"):
            attacker["spd_mult"] = min(1.75, attacker["spd_mult"] + float(fx["buff_spd"]))
        if fx.get("debuff_def"):
            defender["def_mult"] = max(0.55, defender["def_mult"] - float(fx["debuff_def"]))
        if fx.get("shield"):
            attacker["guarding"] = True
        if fx.get("reflect"):
            attacker["reflect"] = True
        if fx.get("burn"):
            defender["dot_turns"] = max(defender["dot_turns"], int(fx["burn"]))
            defender["dot_label"] = "Burn"
        if fx.get("thorns"):
            defender["dot_turns"] = max(defender["dot_turns"], int(fx["thorns"]))
            defender["dot_label"] = "Thorns"

        # High INT grants up to 30% chance to refund 1 SP ("Clever Cast")
        if random.random() < min(0.30, int_val * 0.0022):
            attacker["sp"] = min(attacker["max_sp"], attacker["sp"] + 1)
            result["sp_refund"] = True

    move_name = attacker["ability_name"] if is_skill else "Strike"
    extras = []
    if result["crit"]:
        extras.append("CRIT!")
    if result["healed"] > 0:
        extras.append(f"+{result['healed']}HP")
    if result["sp_refund"]:
        extras.append("+1SP")
    extra_str = (" " + " ".join(extras)) if extras else ""
    result["message"] = f"{attacker['name']} used {move_name}! -{total_dmg}{extra_str}"
    return result