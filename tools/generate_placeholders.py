"""Generates 32x32 pixel-art placeholder PNG sprite sheets for Sparkkit."""

from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "sprites" / "spark_kit"
CELL = 32

# Pixel-art colors (RGBA)
OUTLINE = (22, 14, 34, 255)
BODY    = (145, 98, 225, 255)
LIGHT   = (196, 162, 255, 255)
BELLY   = (240, 232, 255, 255)
EYE     = (255, 236, 110, 255)
CHEEK   = (255, 130, 185, 255)
BERRY   = (255, 95, 115, 255)
LEAF    = (110, 230, 145, 255)
SPARKLE = (255, 245, 160, 255)


def px(surf: pygame.Surface, x: int, y: int, w: int, h: int, color: tuple) -> None:
    pygame.draw.rect(surf, color, pygame.Rect(x, y, w, h))


def draw_sparkkit(
    y_off: int = 0,
    blink: bool = False,
    mouth_open: bool = False,
    leg_phase: int = 0,
    tail_up: bool = False,
    happy_eyes: bool = False,
) -> pygame.Surface:
    """Draws one 32x32 frame of Sparkkit facing right."""
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)

    # Tail (left side because pet faces right)
    tail_y = (17 if tail_up else 19) + y_off
    px(surf, 4, tail_y, 5, 3, OUTLINE)
    px(surf, 5, tail_y + 1, 3, 1, LIGHT)
    px(surf, 3, tail_y - 2, 3, 3, OUTLINE)
    px(surf, 4, tail_y - 1, 1, 1, EYE)  # Glowing spark tip

    # Pointy ears
    px(surf, 10, 8 + y_off, 4, 5, OUTLINE)
    px(surf, 11, 9 + y_off, 2, 3, LIGHT)
    px(surf, 19, 8 + y_off, 4, 5, OUTLINE)
    px(surf, 20, 9 + y_off, 2, 3, LIGHT)

    # Main head/body silhouette
    px(surf, 9, 12 + y_off, 15, 13, OUTLINE)
    px(surf, 10, 13 + y_off, 13, 11, BODY)
    px(surf, 11, 13 + y_off, 11, 2, LIGHT)   # Top highlight
    px(surf, 13, 20 + y_off, 8, 4, BELLY)    # Belly patch

    # Eyes (shifted slightly right to show facing direction)
    if blink:
        px(surf, 14, 17 + y_off, 3, 1, OUTLINE)
        px(surf, 20, 17 + y_off, 2, 1, OUTLINE)
    elif happy_eyes:
        # Cheerful "^ ^" arcs
        px(surf, 14, 16 + y_off, 3, 1, EYE)
        px(surf, 13, 17 + y_off, 1, 1, EYE)
        px(surf, 17, 17 + y_off, 1, 1, EYE)
        px(surf, 19, 16 + y_off, 3, 1, EYE)
        px(surf, 19, 17 + y_off, 1, 1, EYE)
        px(surf, 22, 17 + y_off, 1, 1, EYE)
    else:
        px(surf, 14, 16 + y_off, 2, 3, EYE)
        px(surf, 20, 16 + y_off, 2, 3, EYE)

    # Cheeks
    px(surf, 12, 19 + y_off, 2, 1, CHEEK)
    px(surf, 21, 19 + y_off, 2, 1, CHEEK)

    # Mouth
    if mouth_open:
        px(surf, 18, 19 + y_off, 3, 3, OUTLINE)
        px(surf, 19, 20 + y_off, 1, 1, CHEEK)
    else:
        px(surf, 18, 19 + y_off, 2, 1, OUTLINE)

    # Paws (alternate up/down during walk cycle)
    left_foot_y = 25 + y_off - (1 if leg_phase == 1 else 0)
    right_foot_y = 25 + y_off - (1 if leg_phase == 2 else 0)
    px(surf, 10, left_foot_y, 4, 3, OUTLINE)
    px(surf, 11, left_foot_y, 2, 2, LIGHT)
    px(surf, 19, right_foot_y, 4, 3, OUTLINE)
    px(surf, 20, right_foot_y, 2, 2, LIGHT)

    return surf


def save_strip(filename: str, frames: list[pygame.Surface]) -> None:
    strip = pygame.Surface((CELL * len(frames), CELL), pygame.SRCALPHA)
    for idx, frame in enumerate(frames):
        strip.blit(frame, (idx * CELL, 0))
    pygame.image.save(strip, str(OUT_DIR / filename))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Idle (gentle breathing + blink on frame 4)
    idle_frames = [
        draw_sparkkit(y_off=0, tail_up=False),
        draw_sparkkit(y_off=1, tail_up=True),
        draw_sparkkit(y_off=0, tail_up=False),
        draw_sparkkit(y_off=0, blink=True, tail_up=False),
    ]
    save_strip("idle.png", idle_frames)

    # 2. Walk (4-frame bounce & alternating paws)
    walk_frames = [
        draw_sparkkit(y_off=0, leg_phase=1, tail_up=True),
        draw_sparkkit(y_off=-1, leg_phase=0, tail_up=False),
        draw_sparkkit(y_off=0, leg_phase=2, tail_up=True),
        draw_sparkkit(y_off=-1, leg_phase=0, tail_up=False),
    ]
    save_strip("walk.png", walk_frames)

    # 3. Eat (pixel berry floats in and gets chomped)
    eat_frames = []
    for i in range(4):
        f = draw_sparkkit(y_off=(1 if i % 2 else 0), mouth_open=(i in (1, 2)), tail_up=True)
        if i == 0:
            px(f, 26, 17, 4, 4, BERRY)
            px(f, 27, 15, 2, 2, LEAF)
        elif i == 1:
            px(f, 23, 18, 4, 4, BERRY)
            px(f, 24, 16, 2, 2, LEAF)
        elif i == 2:
            px(f, 21, 19, 2, 2, BERRY)  # Half-eaten!
        eat_frames.append(f)
    save_strip("eat.png", eat_frames)

    # 4. Happy (excited hop + sparkles)
    happy_frames = []
    for i in range(4):
        hop = -4 if i in (1, 2) else 0
        f = draw_sparkkit(y_off=hop, happy_eyes=True, mouth_open=(i in (1, 2)), tail_up=True)
        if i in (1, 2):
            px(f, 6, 4 + i, 2, 2, SPARKLE)
            px(f, 25, 6 - i, 2, 2, SPARKLE)
            px(f, 16, 2, 2, 2, SPARKLE)
        happy_frames.append(f)
    save_strip("happy.png", happy_frames)

    print(f"Generated 4 sprite sheets in: {OUT_DIR}")


if __name__ == "__main__":
    main()