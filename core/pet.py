import random
import time

# Set to 60.0 while testing so 1 real second = 1 in-game minute (reset to 1.0 for normal play)
TIME_SCALE = 1.0

MAX_POOPS = 4
POOP_INTERVAL_SEC = 90 * 60       # 1 poop roughly every 90 awake minutes
MAX_OFFLINE_SEC = 48 * 3600       # Cap offline catch-up at 48 hours
HUG_COOLDOWN_SEC = 6.0            # Prevents spamming bond infinitely in 1 second


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


class Pet:
    """Tracks care stats, bond, poop spawns, sleep, age, and offline time decay."""

    def __init__(self, data: dict | None = None):
        now = time.time()
        data = data or {}

        self.name: str = data.get("name", "SPARKKIT")
        self.species_id: str = data.get("species_id", "spark_kit")
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

        # Ready for Phase 2 & 3 (training, branching evolutions, battles)
        self.care_mistakes: int = int(data.get("care_mistakes", 0))
        self.battle_stats: dict = dict(
            data.get("battle_stats", {"atk": 8, "def": 6, "spd": 10, "int": 6})
        )

    @property
    def age_hours(self) -> int:
        return max(0, int((time.time() - self.born_at) // 3600))

    def get_need_bubble(self) -> str | None:
        """Returns the most urgent need icon to show above the pet, or None."""
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
        return {
            "name": self.name,
            "species_id": self.species_id,
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
            "battle_stats": self.battle_stats,
        }

    def _spawn_poop(self) -> None:
        if len(self.poops) >= MAX_POOPS:
            return
        slots = [x for x in range(24, 282, 22) if all(abs(x - p) >= 18 for p in self.poops)]
        spot = random.choice(slots) if slots else random.randint(24, 280)
        self.poops.append(spot)
        self.clean = clamp(self.clean - 12.0)

    def _simulate_slice(self, sim_seconds: float) -> None:
        if not self.alive or sim_seconds <= 0:
            return

        dt_min = sim_seconds / 60.0
        poop_penalty = len(self.poops)

        if self.sleeping:
            self.energy = clamp(self.energy + dt_min * 0.35)
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

    def apply_offline_time(self, now: float | None = None) -> float:
        now = now if now is not None else time.time()
        raw_elapsed = max(0.0, now - self.last_update)
        sim_elapsed = min(raw_elapsed * TIME_SCALE, float(MAX_OFFLINE_SEC))

        remaining = sim_elapsed
        while remaining > 0 and self.alive:
            step = min(60.0, remaining)
            self._simulate_slice(step)
            remaining -= step

        self.last_update = now
        return raw_elapsed

    def update(self, dt: float) -> None:
        self._simulate_slice(dt * TIME_SCALE)
        self.last_update = time.time()

    # --- Care Actions ---

    def feed(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, "Shh! Sparkkit is sleeping."
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
            return False, "Shh! Sparkkit is sleeping."
        if self.hunger >= 99.0 and self.happy >= 99.0:
            return False, "Sparkkit is already stuffed!"

        self.hunger = clamp(self.hunger + 10.0)
        self.happy = clamp(self.happy + 14.0)
        self.clean = clamp(self.clean - 2.0)
        self.bond = min(999, self.bond + 2)
        self.poop_timer += 5 * 60
        return True, "Star Treat! +14 Happy +2 Bond"

    def play(self) -> tuple[bool, str]:
        if not self.alive:
            return False, "Press [R] to hatch a new egg."
        if self.sleeping:
            return False, "Wake Sparkkit first [S]."
        if self.energy < 15.0:
            return False, "Too tired! Put to bed [S]."

        self.happy = clamp(self.happy + 22.0)
        self.energy = clamp(self.energy - 12.0)
        self.hunger = clamp(self.hunger - 5.0)
        self.bond = min(999, self.bond + 2)
        return True, "Ball time! +22 Happy"

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
            return True, "Sparkkit purrs! +3 Bond"
        return True, "Sparkkit loves the pets!"

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