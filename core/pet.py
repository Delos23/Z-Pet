from datetime import datetime
import random
import time

DEFAULT_TIME_SCALE = 1.0

MAX_POOPS = 4
POOP_INTERVAL_SEC = 90 * 60       # 1 poop roughly every 90 awake minutes
MAX_OFFLINE_SEC = 48 * 3600       # Cap offline catch-up at 48 hours
HUG_COOLDOWN_SEC = 6.0

MAX_DAILY_TRAINS = 3              # Prevents maxing stats in a single day
SLEEP_ENERGY_PER_MIN = 1.25       # Full 0->100% recharge in ~80 min (~+25 in 20 min)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


class Pet:
    """Tracks care stats, color, bond, battle stats, daily training limit, and offline decay."""

    def __init__(self, data: dict | None = None):
        now = time.time()
        data = data or {}

        self.name: str = data.get("name", "SPARKKIT")
        self.species_id: str = data.get("species_id", "spark_kit")
        self.color: str = str(data.get("color", "purple"))
        self.stage: str = data.get("stage", "baby")

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

        # Floor poops stored as X coordinates on the 320px room floor
        self.poops: list[int] = list(data.get("poops", []))
        self.poop_timer: float = float(data.get("poop_timer", 0.0))

        # Phase 2 & 3 progression stats + daily training cap
        self.care_mistakes: int = int(data.get("care_mistakes", 0))
        self.training_sessions: int = int(data.get("training_sessions", 0))
        self.trains_today: int = int(data.get("trains_today", 0))
        self.last_train_date: str = str(data.get("last_train_date", ""))
        self.high_score: int = int(data.get("high_score", 0))
        self.battle_stats: dict = dict(
            data.get("battle_stats", {"atk": 8, "def": 6, "spd": 10, "int": 6})
        )

    @property
    def age_hours(self) -> int:
        return max(0, int((time.time() - self.born_at) // 3600))

    def _sync_daily_trains(self) -> None:
        """Resets the daily training count when the calendar date changes."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_train_date != today:
            self.last_train_date = today
            self.trains_today = 0

    @property
    def trainings_remaining(self) -> int:
        self._sync_daily_trains()
        return max(0, MAX_DAILY_TRAINS - self.trains_today)

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

        if self.sleeping:
            self.energy = clamp(self.energy + dt_min * SLEEP_ENERGY_PER_MIN)
            self.hunger = clamp(self.hunger - dt_min * 0.04)
            self.happy = clamp(self.happy - dt_min * 0.02)
            self.clean = clamp(self.clean - dt_min * (0.02 + poop_penalty * 0.05))
        else:
            self.hunger = clamp(self.hunger - dt_min * 0.15)
            self.happy = clamp(self.happy - dt_min * (0.12 + poop_penalty * 0.06))
            self.energy = clamp(self.energy - dt_min * 0.10)
            self.clean = clamp(self.clean - dt_min * (0.05 + poop_penalty * 0.12))

            self.poop_timer += sim_seconds
            while self.poop_timer >= POOP_INTERVAL_SEC:
                self.poop_timer -= POOP_INTERVAL_SEC
                self._spawn_poop()

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

    # --- Care Actions ---

    def feed(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Shh! {self.name} is sleeping."
        if self.hunger >= 99.0:
            return False, "Too full for a meal!"

        self.hunger = clamp(self.hunger + 25.0)
        self.clean = clamp(self.clean - 4.0)
        self.bond = min(999, self.bond + 1)
        self.poop_timer += 10 * 60
        return True, "Yummy meal! +25 Hunger"

    def give_treat(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Shh! {self.name} is sleeping."
        if self.hunger >= 99.0 and self.happy >= 99.0:
            return False, f"{self.name} is already stuffed!"

        self.hunger = clamp(self.hunger + 10.0)
        self.happy = clamp(self.happy + 14.0)
        self.clean = clamp(self.clean - 2.0)
        self.bond = min(999, self.bond + 2)
        self.poop_timer += 5 * 60
        return True, "Star Treat! +14 Happy +2 Bond"

    def can_play(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, f"Wake {self.name} first [S]."
        if self.energy < 15.0:
            return False, "Too tired to play! [S] Bed."
        return True, ""

    def complete_minigame(self, score: int) -> dict:
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

        return {
            "score": score,
            "happy_gain": happy_gain,
            "bond_gain": bond_gain,
            "spd_bonus": spd_bonus,
            "is_new_best": is_new_best,
            "high_score": self.high_score,
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
        old_val = int(self.battle_stats.get(stat_key, 5))

        if drill_points >= 5:
            grade, stat_gain, bond_gain, happy_gain = "PERFECT!", 3, 4, 10
        elif drill_points >= 3:
            grade, stat_gain, bond_gain, happy_gain = "GREAT!", 2, 3, 7
        elif drill_points >= 1:
            grade, stat_gain, bond_gain, happy_gain = "GOOD", 1, 2, 4
        else:
            grade, stat_gain, bond_gain, happy_gain = "NICE TRY", 1, 1, 2

        new_val = min(99, old_val + stat_gain)
        self.battle_stats[stat_key] = new_val
        self.training_sessions += 1
        self.trains_today += 1

        self.energy = clamp(self.energy - 12.0)
        self.hunger = clamp(self.hunger - 7.0)
        self.happy = clamp(self.happy + happy_gain)
        self.bond = min(999, self.bond + bond_gain)

        return {
            "stat_key": stat_key,
            "old_val": old_val,
            "new_val": new_val,
            "stat_gain": new_val - old_val,
            "grade": grade,
            "bond_gain": bond_gain,
            "happy_gain": happy_gain,
            "remaining_today": self.trainings_remaining,
        }

    def hug(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, "Sweet dreams... (sleeping)"

        now = time.time()
        self.happy = clamp(self.happy + 6.0)
        if now - self._last_hug_time >= HUG_COOLDOWN_SEC:
            self._last_hug_time = now
            self.bond = min(999, self.bond + 3)
            return True, f"{self.name} purrs! +3 Bond"
        return True, f"{self.name} loves the pets!"

    def clean_room(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."

        removed = len(self.poops)
        if removed == 0 and self.clean >= 98.0:
            return False, "Room is already spotless!"

        self.poops.clear()
        self.clean = 100.0
        if removed > 0:
            self.happy = clamp(self.happy + 8.0)
            return True, f"Cleaned {removed} mess{'es' if removed > 1 else ''}!"
        return True, "Squeaky clean!"

    def toggle_sleep(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."

        self.sleeping = not self.sleeping
        return True, "Tucked into bed... Zzz" if self.sleeping else "Good morning!"