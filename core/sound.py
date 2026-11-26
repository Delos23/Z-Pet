"""Lightweight procedural 8-bit retro sound engine for Z-Pet (zero external audio files)."""

from array import array
import math
import random
import pygame

SAMPLE_RATE = 22050
_ENABLED = True
_READY = False
_SOUNDS: dict[str, pygame.mixer.Sound] = {}


def _gen_tone(
    freq: float,
    dur_ms: int,
    wave: str = "square",
    vol: float = 0.24,
    slide_to: float | None = None,
    decay: bool = True,
) -> array:
    """Synthesizes a 16-bit signed mono chiptune tone."""
    n = max(1, int(SAMPLE_RATE * dur_ms / 1000))
    buf = array("h")
    phase = 0.0
    rng = random.Random(int(freq) + dur_ms)

    for i in range(n):
        t = i / n
        if freq <= 0:
            buf.append(0)
            continue

        cur_f = freq + (slide_to - freq) * t if slide_to is not None else freq
        phase += cur_f / SAMPLE_RATE
        frac = phase - math.floor(phase)

        if wave == "square":
            raw = 1.0 if frac < 0.5 else -1.0
        elif wave == "pulse25":
            raw = 1.0 if frac < 0.25 else -1.0
        elif wave == "triangle":
            raw = 4.0 * abs(frac - 0.5) - 1.0
        elif wave == "noise":
            raw = rng.uniform(-1.0, 1.0)
        else:
            raw = math.sin(2.0 * math.pi * phase)

        env = (1.0 - t * 0.85) if decay else 1.0
        if i < 40:
            env *= i / 40.0  # Soft attack prevents speaker clicks
        sample = int(max(-1.0, min(1.0, raw * vol * env)) * 32767)
        buf.append(sample)
    return buf


def _seq(steps: list[tuple]) -> pygame.mixer.Sound:
    """Chains (freq, dur_ms, wave, vol, slide_to) tuples into one Sound."""
    out = array("h")
    for step in steps:
        freq = step[0]
        dur_ms = step[1]
        wave = step[2] if len(step) > 2 else "square"
        vol = step[3] if len(step) > 3 else 0.22
        slide_to = step[4] if len(step) > 4 else None
        out.extend(_gen_tone(freq, dur_ms, wave=wave, vol=vol, slide_to=slide_to))
    return pygame.mixer.Sound(buffer=out.tobytes())


def _build_bank() -> dict[str, pygame.mixer.Sound]:
    """Generates all retro sound effects once at startup (~50ms total)."""
    return {
        # UI & Navigation
        "click": _seq([(880, 22, "pulse25", 0.16)]),
        "select": _seq([(660, 40, "square", 0.18), (990, 55, "square", 0.20)]),
        "back": _seq([(520, 40, "triangle", 0.22), (340, 55, "triangle", 0.20)]),
        "error": _seq([(180, 70, "square", 0.22), (0, 25), (140, 95, "square", 0.22)]),

        # Care Actions
        "feed": _seq([
            (392, 55, "square", 0.20),
            (523, 55, "square", 0.20),
            (659, 85, "square", 0.22),
        ]),
        "treat": _seq([
            (587, 45, "pulse25", 0.18),
            (880, 45, "pulse25", 0.20),
            (1175, 95, "pulse25", 0.22),
        ]),
        "clean": _seq([
            (480, 65, "triangle", 0.24, 960),
            (620, 80, "triangle", 0.24, 1240),
        ]),
        "hug": _seq([
            (523, 55, "triangle", 0.26),
            (659, 60, "triangle", 0.26),
            (784, 90, "triangle", 0.26),
        ]),
        "sleep": _seq([
            (523, 95, "triangle", 0.22),
            (440, 95, "triangle", 0.20),
            (349, 160, "triangle", 0.18),
        ]),
        "wake": _seq([
            (440, 65, "triangle", 0.22),
            (587, 65, "triangle", 0.22),
            (880, 120, "square", 0.18),
        ]),

        # Mini-game & Drills
        "catch": _seq([(784, 40, "pulse25", 0.20), (1175, 65, "pulse25", 0.22)]),
        "bolt": _seq([(240, 110, "noise", 0.24), (130, 90, "square", 0.22)]),

        # Battle Arena
        "hit": _seq([(190, 50, "noise", 0.28), (160, 75, "square", 0.24, 75)]),
        "crit": _seq([
            (320, 40, "noise", 0.30),
            (740, 50, "square", 0.26, 220),
            (180, 90, "noise", 0.26),
        ]),
        "skill": _seq([
            (340, 75, "pulse25", 0.22, 920),
            (920, 95, "square", 0.24, 1320),
        ]),
        "guard": _seq([(540, 45, "triangle", 0.26), (820, 85, "triangle", 0.24)]),
        "dodge": _seq([(620, 65, "triangle", 0.22, 1180)]),
        "heal": _seq([
            (523, 60, "triangle", 0.22),
            (659, 60, "triangle", 0.22),
            (1046, 110, "triangle", 0.24),
        ]),

        # Boss Intro, Victory & Defeat
        "boss": _seq([
            (147, 110, "square", 0.28),
            (0, 25),
            (147, 110, "square", 0.28),
            (0, 25),
            (139, 130, "square", 0.28),
            (220, 220, "square", 0.30, 110),
        ]),
        "victory": _seq([
            (523, 75, "square", 0.22),
            (659, 75, "square", 0.22),
            (784, 75, "square", 0.22),
            (1046, 220, "square", 0.26),
        ]),
        "defeat": _seq([
            (392, 110, "triangle", 0.24),
            (349, 110, "triangle", 0.22),
            (311, 120, "triangle", 0.22),
            (261, 240, "triangle", 0.20),
        ]),

        # Progression Milestones
        "level_up": _seq([
            (523, 60, "pulse25", 0.22),
            (659, 60, "pulse25", 0.22),
            (784, 60, "pulse25", 0.22),
            (1046, 80, "square", 0.24),
            (1318, 170, "square", 0.24),
        ]),
        "evolve": _seq([
            (392, 75, "pulse25", 0.22),
            (494, 75, "pulse25", 0.22),
            (587, 75, "pulse25", 0.22),
            (784, 90, "square", 0.24),
            (659, 70, "square", 0.22),
            (784, 85, "square", 0.24),
            (1046, 260, "square", 0.28),
        ]),
    }


def init(enabled: bool = True) -> bool:
    """Initializes the mixer safely; silently disables audio if no device exists."""
    global _ENABLED, _READY, _SOUNDS
    _ENABLED = bool(enabled)
    try:
        current = pygame.mixer.get_init()
        if current != (SAMPLE_RATE, -16, 1):
            if current is not None:
                pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        pygame.mixer.set_num_channels(8)
        _SOUNDS = _build_bank()
        _READY = True
    except pygame.error:
        _READY = False
        _SOUNDS = {}
    return _READY


def set_enabled(enabled: bool) -> None:
    global _ENABLED
    _ENABLED = bool(enabled)
    if not _ENABLED and _READY:
        try:
            pygame.mixer.stop()
        except pygame.error:
            pass


def is_enabled() -> bool:
    return _ENABLED


def play(name: str) -> None:
    """Plays a named sound effect if audio is enabled and initialized."""
    if not _ENABLED or not _READY:
        return
    snd = _SOUNDS.get(name)
    if snd is not None:
        try:
            snd.play()
        except pygame.error:
            pass