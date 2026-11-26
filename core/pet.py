from datetime import datetime
import random
import time

from core.species import CARE_PATH_META, evaluate_care_path, find_evolution, get_personality, get_species

DEFAULT_TIME_SCALE = 1.0

MAX_POOPS = 4
POOP_INTERVAL_SEC = 90 * 60
MAX_OFFLINE_SEC = 48 * 3600
HUG_COOLDOWN_SEC = 6.0

MAX_DAILY_TRAINS = 3
SLEEP_ENERGY_PER_MIN = 1.25
MAX_LEVEL = 30
MAX_STAT = 150

# Leaving severe needs (<15%) or 3+ poops unattended for 30 sim-minutes adds 1 care mistake
NEGLECT_MISTAKE_SEC = 30 * 60


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


class Pet:
    """Tracks care stats, species, personality, base color, XP/level, care mistakes, and evolution."""

    def __init__(self, data: dict | None = None):
        now = time.time()
        data = data or {}

        self.species_id: str = str(data.get("species_id", "spark_kit"))
        sp = get_species(self.species_id)

        self.name: str = str(data.get("name") or sp["default_name"])
        self.color: str = str(data.get("color", "purple"))
        self.stage: str = str(data.get("stage", sp.get("stage", "baby")))

        # Leveling & signature ability (starters now begin with their own ability too!)
        self.level: int = max(1, min(MAX_LEVEL, int(data.get("level", 1))))
        self.xp: int = max(0, int(data.get("xp", 0)))
        default_ability = sp["ability"]["name"] if sp.get("ability") else None
        self.ability: str | None = data.get("ability") or default_ability

        # Core care stats (0.0 to 100.0)
        self.hunger: float = float(data.get("hunger", 85.0))
        self.happy: float = float(data.get("happy", 85.0))
        self.energy: float = float(data.get("energy", 90.0))
        self.clean: float = float(data.get("clean", 100.0))

        self.sleeping: bool = bool(data.get("sleeping", False))
        self.alive: bool = bool(data.get("alive", True))
        self.bond: int = int(data.get("bond", 0))

        # Timestamps
        self.born_at: float = float(data.get("born_at", now))
        self.last_update: float = float(data.get("last_update", now))
        self._last_hug_time: float = 0.0

        # Floor poops & care-mistake neglect tracker
        self.poops: list[int] = list(data.get("poops", []))
        self.poop_timer: float = float(data.get("poop_timer", 0.0))
        self.care_mistakes: int = int(data.get("care_mistakes", 0))
        self.neglect_timer: float = float(data.get("neglect_timer", 0.0))

        # Training, mini-game & battle stats
        self.training_sessions: int = int(data.get("training_sessions", 0))
        self.trains_today: int = int(data.get("trains_today", 0))
        self.last_train_date: str = str(data.get("last_train_date", ""))
        self.high_score: int = int(data.get("high_score", 0))
        self.battle_stats: dict = dict(data.get("battle_stats", sp["base_stats"]))

    @property
    def personality(self) -> dict:
        return get_personality(self.species_id)

    @property
    def age_hours(self) -> int:
        return max(0, int((time.time() - self.born_at) // 3600))

    @property
    def xp_to_next(self) -> int:
     return 20 + self.level * 25

    def _sync_daily_trains(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_train_date != today:
            self.last_train_date = today
            self.trains_today = 0

    @property
    def trainings_remaining(self) -> int:
        self._sync_daily_trains()
        return max(0, MAX_DAILY_TRAINS - self.trains_today)

    def add_xp(self, amount: int) -> dict:
        amount = max(0, int(amount))
        if not self.alive or self.level >= MAX_LEVEL or amount == 0:
            return {
                "xp_gain": 0,
                "leveled_up": False,
                "new_level": self.level,
                "stat_ups": {},
            }

        self.xp += amount
        leveled_up = False
        total_ups = {"atk": 0, "def": 0, "spd": 0, "int": 0}
        growth = get_species(self.species_id).get("growth", {"atk": 1, "def": 1, "spd": 1, "int": 1})

        while self.level < MAX_LEVEL and self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            leveled_up = True
            for stat_k in ("atk", "def", "spd", "int"):
                inc = int(growth.get(stat_k, 1))
                old_v = int(self.battle_stats.get(stat_k, 5))
                new_v = min(99, old_v + inc)
                self.battle_stats[stat_k] = new_v
                total_ups[stat_k] += new_v - old_v

        if self.level >= MAX_LEVEL:
            self.xp = 0

        return {
            "xp_gain": amount,
            "leveled_up": leveled_up,
            "new_level": self.level,
            "stat_ups": total_ups,
        }

    def check_evolution_ready(self) -> str | None:
        return find_evolution(self)

    def evolve(self, target_species_id: str) -> dict:
        """Transforms the pet into its care-driven adult form and unlocks its evolved ability."""
        care_path = evaluate_care_path(self, final_check=True)
        care_label = CARE_PATH_META.get(care_path, ("Radiant", (105, 225, 145)))[0]

        old_sp = get_species(self.species_id)
        new_sp = get_species(target_species_id)

        self.species_id = target_species_id
        self.stage = str(new_sp.get("stage", "adult"))

        bonus = new_sp.get("evolve_bonus", {})
        applied_bonus: dict[str, int] = {}
        for stat_k in ("atk", "def", "spd", "int"):
            inc = int(bonus.get(stat_k, 2))
            old_v = int(self.battle_stats.get(stat_k, 10))
            new_v = min(99, old_v + inc)
            self.battle_stats[stat_k] = new_v
            applied_bonus[stat_k] = new_v - old_v

        ability_info = new_sp.get("ability")
        self.ability = ability_info["name"] if ability_info else None

        self.happy = 100.0
        self.energy = clamp(self.energy + 25.0)
        self.bond = min(999, self.bond + 5)

        return {
            "care_path": care_path,
            "care_label": care_label,
            "new_stage": self.stage,
            "old_species_name": old_sp["name"],
            "new_species_name": new_sp["name"],
            "stat_bonus": applied_bonus,
            "ability_name": self.ability or "None",
            "ability_desc": ability_info["desc"] if ability_info else "",
        }

    def get_need_bubble(self) -> str | None:
        if not self.alive or self.sleeping:
            return None
        if self.hunger < 35.0:
            return "hunger"
        if len(self.poops) > 0 or self.clean < 40.0:
            return "clean"
        if self.energy < 30.0:
            return "energy"
        if self.happy < 35.0:
            return "happy"
        return None

    def to_dict(self) -> dict:
        self._sync_daily_trains()
        return {
            "name": self.name,
            "species_id": self.species_id,
            "color": self.color,
            "stage": self.stage,
            "level": self.level,
            "xp": self.xp,
            "ability": self.ability,
            "hunger": round(self.hunger, 2),
            "happy": round(self.happy, 2),
            "energy": round(self.energy, 2),
            "clean": round(self.clean, 2),
            "sleeping": self.sleeping,
            "alive": self.alive,
            "bond": self.bond,
            "born_at": self.born_at,
            "last_update": self.last_update,
            "poops": self.poops,
            "poop_timer": round(self.poop_timer, 2),
            "care_mistakes": self.care_mistakes,
            "neglect_timer": round(self.neglect_timer, 2),
            "training_sessions": self.training_sessions,
            "trains_today": self.trains_today,
            "last_train_date": self.last_train_date,
            "high_score": self.high_score,
            "battle_stats": self.battle_stats,
        }

    def _spawn_poop(self) -> None:
        if len(self.poops) >= MAX_POOPS:
            return
        slots = [x for x in range(28, 204, 22) if all(abs(x - p) >= 18 for p in self.poops)]
        spot = random.choice(slots) if slots else random.randint(28, 198)
        self.poops.append(spot)
        self.clean = clamp(self.clean - 12.0)

    def _simulate_slice(self, sim_seconds: float) -> None:
        if not self.alive or sim_seconds <= 0:
            return

        dt_min = sim_seconds / 60.0
        poop_penalty = len(self.poops)
        p = self.personality

        if self.sleeping:
            self.energy = clamp(self.energy + dt_min * SLEEP_ENERGY_PER_MIN * p["sleep_mult"])
            self.hunger = clamp(self.hunger - dt_min * 0.04 * p["hunger_decay"])
            self.happy = clamp(self.happy - dt_min * 0.02 * p["happy_decay"])
            self.clean = clamp(self.clean - dt_min * (0.02 + poop_penalty * 0.05) * p["clean_decay"])
        else:
            self.hunger = clamp(self.hunger - dt_min * 0.15 * p["hunger_decay"])
            self.happy = clamp(self.happy - dt_min * (0.12 + poop_penalty * 0.06) * p["happy_decay"])
            self.energy = clamp(self.energy - dt_min * 0.10 * p["energy_decay"])
            self.clean = clamp(self.clean - dt_min * (0.05 + poop_penalty * 0.12) * p["clean_decay"])

            self.poop_timer += sim_seconds
            while self.poop_timer >= POOP_INTERVAL_SEC:
                self.poop_timer -= POOP_INTERVAL_SEC
                self._spawn_poop()

            # Track sustained neglect for Care Mistakes (drives Wild vs Radiant evolution)
            neglected = (
                self.hunger < 15.0
                or self.happy < 15.0
                or self.clean < 15.0
                or len(self.poops) >= 3
            )
            if neglected:
                self.neglect_timer += sim_seconds
                while self.neglect_timer >= NEGLECT_MISTAKE_SEC:
                    self.neglect_timer -= NEGLECT_MISTAKE_SEC
                    self.care_mistakes += 1
            else:
                self.neglect_timer = max(0.0, self.neglect_timer - sim_seconds * 0.5)

        if self.hunger <= 0.0 or (self.energy <= 0.0 and self.clean <= 0.0):
            self.care_mistakes += 1
            self.alive = False

    def apply_offline_time(
        self,
        now: float | None = None,
        time_scale: float = DEFAULT_TIME_SCALE,
    ) -> float:
        now = now if now is not None else time.time()
        raw_elapsed = max(0.0, now - self.last_update)
        sim_elapsed = min(raw_elapsed * time_scale, float(MAX_OFFLINE_SEC))

        remaining = sim_elapsed
        while remaining > 0 and self.alive:
            step = min(60.0, remaining)
            self._simulate_slice(step)
            remaining -= step

        self.last_update = now
        return raw_elapsed

    def update(self, dt: float, time_scale: float = DEFAULT_TIME_SCALE) -> None:
        self._simulate_slice(dt * time_scale)
        self.last_update = time.time()

    # --- Care Actions (Personality-aware!) ---

    def feed(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Shh! {self.name} is sleeping."
        if self.hunger >= 99.0:
            return False, "Too full for a meal!"

        p = self.personality
        meal_gain = 25.0 + p["meal_bonus"]
        self.hunger = clamp(self.hunger + meal_gain)
        self.clean = clamp(self.clean - 4.0)
        self.bond = min(999, self.bond + 1)
        self.poop_timer += 10 * 60
        xp_amt = round(6 * p["care_xp_mult"])
        xp_res = self.add_xp(xp_amt)
        if xp_res["leveled_up"]:
            return True, f"LEVEL UP! {self.name} is Lv.{self.level}!"
        return True, f"Yummy meal! +{int(meal_gain)} Hunger +{xp_amt} XP"

    def give_treat(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Shh! {self.name} is sleeping."
        if self.hunger >= 99.0 and self.happy >= 99.0:
            return False, f"{self.name} is already stuffed!"

        p = self.personality
        bond_gain = 2 + p["hug_bond_bonus"]
        self.hunger = clamp(self.hunger + 10.0)
        self.happy = clamp(self.happy + 14.0)
        self.clean = clamp(self.clean - 2.0)
        self.bond = min(999, self.bond + bond_gain)
        self.poop_timer += 5 * 60
        xp_amt = round(4 * p["care_xp_mult"])
        xp_res = self.add_xp(xp_amt)
        if xp_res["leveled_up"]:
            return True, f"LEVEL UP! {self.name} is Lv.{self.level}!"
        return True, f"Star Treat! +14 Happy +{bond_gain} Bond"

    def can_play(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Wake {self.name} first [S]."
        if self.energy < 15.0:
            return False, "Too tired to play! [S] Bed."
        return True, ""

    def complete_minigame(self, score: int) -> dict:
        p = self.personality
        score = max(0, int(score))
        happy_gain = min(35, 10 + score * 2)
        bond_gain = 2 if score < 6 else (3 if score < 12 else 5)
        spd_bonus = 1 if score >= 12 else 0

        self.happy = clamp(self.happy + happy_gain)
        self.energy = clamp(self.energy - 12.0)
        self.hunger = clamp(self.hunger - 6.0)
        self.bond = min(999, self.bond + bond_gain)

        if spd_bonus:
            self.battle_stats["spd"] = min(99, self.battle_stats.get("spd", 10) + spd_bonus)

        is_new_best = score > self.high_score
        if is_new_best:
            self.high_score = score

        xp_amt = round((10 + score * 2) * p["play_xp_mult"])
        xp_res = self.add_xp(xp_amt)

        return {
            "score": score,
            "happy_gain": happy_gain,
            "bond_gain": bond_gain,
            "spd_bonus": spd_bonus,
            "is_new_best": is_new_best,
            "high_score": self.high_score,
            "xp_gain": xp_res["xp_gain"],
            "leveled_up": xp_res["leveled_up"],
            "new_level": xp_res["new_level"],
        }

    def can_train(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Wake {self.name} first [S]."
        if self.trainings_remaining <= 0:
            return False, f"Daily limit ({MAX_DAILY_TRAINS}/{MAX_DAILY_TRAINS}) reached!"
        if self.energy < 15.0:
            return False, "Too tired to train! [S] Bed."
        if self.hunger < 15.0:
            return False, "Too hungry to train! [F] Eat."
        return True, ""

    def apply_training(self, stat_key: str, drill_points: int) -> dict:
        self._sync_daily_trains()
        p = self.personality
        old_val = int(self.battle_stats.get(stat_key, 5))

        if drill_points >= 5:
            grade = "PERFECT!"
            stat_gain = 3 + p["perfect_stat_bonus"]
            bond_gain, happy_gain = 4, 10
        elif drill_points >= 3:
            grade, stat_gain, bond_gain, happy_gain = "GREAT!", 2, 3, 7
        elif drill_points >= 1:
            grade, stat_gain, bond_gain, happy_gain = "GOOD", 1, 2, 4
        else:
            grade, stat_gain, bond_gain, happy_gain = "NICE TRY", 1, 1, 2

        new_val = min(99, old_val + stat_gain)
        actual_gain = new_val - old_val
        self.battle_stats[stat_key] = new_val
        self.training_sessions += 1
        self.trains_today += 1

        self.energy = clamp(self.energy - 12.0)
        self.hunger = clamp(self.hunger - 7.0)
        self.happy = clamp(self.happy + happy_gain)
        self.bond = min(999, self.bond + bond_gain)

        xp_amt = round((15 + drill_points * 4) * p["train_xp_mult"])
        xp_res = self.add_xp(xp_amt)

        return {
            "stat_key": stat_key,
            "old_val": old_val,
            "new_val": int(self.battle_stats.get(stat_key, new_val)),
            "stat_gain": actual_gain,
            "grade": grade,
            "bond_gain": bond_gain,
            "happy_gain": happy_gain,
            "remaining_today": self.trainings_remaining,
            "xp_gain": xp_res["xp_gain"],
            "leveled_up": xp_res["leveled_up"],
            "new_level": xp_res["new_level"],
        }

    def hug(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, "Sweet dreams... (sleeping)"

        p = self.personality
        now = time.time()
        self.happy = clamp(self.happy + 6.0)
        if now - self._last_hug_time >= HUG_COOLDOWN_SEC:
            self._last_hug_time = now
            bond_gain = 3 + p["hug_bond_bonus"]
            self.bond = min(999, self.bond + bond_gain)
            xp_amt = round(5 * p["care_xp_mult"])
            xp_res = self.add_xp(xp_amt)
            if xp_res["leveled_up"]:
                return True, f"LEVEL UP! {self.name} is Lv.{self.level}!"
            return True, f"{self.name} purrs! +{bond_gain} Bond +{xp_amt} XP"
        return True, f"{self.name} loves the pets!"

    def clean_room(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."

        removed = len(self.poops)
        if removed == 0 and self.clean >= 98.0:
            return False, "Room is already spotless!"

        p = self.personality
        self.poops.clear()
        self.clean = 100.0
        self.neglect_timer = 0.0
        if removed > 0:
            self.happy = clamp(self.happy + 8.0)
            xp_amt = round(8 * removed * p["care_xp_mult"])
            xp_res = self.add_xp(xp_amt)
            if xp_res["leveled_up"]:
                return True, f"LEVEL UP! {self.name} is Lv.{self.level}!"
            return True, f"Cleaned {removed} mess{'es' if removed > 1 else ''}! +{xp_amt} XP"
        return True, "Squeaky clean!"

    def toggle_sleep(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."

        self.sleeping = not self.sleeping
        return True, "Tucked into bed... Zzz" if self.sleeping else "Good morning!"