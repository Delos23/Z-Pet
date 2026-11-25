"""Generates 32x32 pixel-art placeholder PNG sprite sheets for Sparkkit."""

from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "sprites" / "spark_kit"
CELL = 32

# Pixel-art palette (RGBA)
OUTLINE = (22, 14, 34, 255)
BODY    = (145, 98, 225, 255)
LIGHT   = (196, 162, 255, 255)
BELLY   = (240, 232, 255, 255)
EYE     = (255, 236, 110, 255)
CHEEK   = (255, 130, 185, 255)
SPARKLE = (255, 245, 160, 255)

# Props palette
BED_RIM    = (88, 56, 138, 255)
BED_INNER  = (132, 98, 186, 255)
PILLOW     = (242, 236, 252, 255)
PILLOW_SHD = (204, 192, 226, 255)
BOWL_MAIN  = (220, 82, 108, 255)
BOWL_RIM   = (255, 140, 162, 255)
FOOD_GOLD  = (232, 166, 72, 255)
FOOD_DARK  = (176, 108, 42, 255)
TREAT_PINK = (255, 110, 185, 255)
TREAT_GLOW = (255, 236, 128, 255)
BALL_CYAN  = (88, 220, 245, 255)
BALL_LIGHT = (190, 248, 255, 255)
BALL_GOLD  = (255, 212, 84, 255)


def px(surf: pygame.Surface, x: int, y: int, w: int, h: int, color: tuple) -> None:
    pygame.draw.rect(surf, color, pygame.Rect(x, y, w, h))


def draw_bed_back(surf: pygame.Surface) -> None:
    """Draws the back rim, cushion, and pillow of the pet bed."""
    px(surf, 2, 20, 28, 9, OUTLINE)
    px(surf, 3, 21, 26, 7, BED_RIM)
    px(surf, 5, 21, 22, 4, BED_INNER)

    px(surf, 19, 18, 9, 6, OUTLINE)
    px(surf, 20, 19, 7, 4, PILLOW)
    px(surf, 20, 22, 7, 1, PILLOW_SHD)


def draw_bed_front(surf: pygame.Surface) -> None:
    """Draws the front rim of the pet bed so Sparkkit looks tucked inside."""
    px(surf, 4, 24, 24, 4, OUTLINE)
    px(surf, 5, 25, 22, 2, BED_RIM)


def draw_sparkkit_on(
    surf: pygame.Surface,
    x_off: int = 0,
    y_off: int = 0,
    eyes: str = "open",
    mouth_open: bool = False,
    leg_phase: int = 0,
    tail_up: bool = False,
) -> None:
    """Draws standing/jumping Sparkkit onto an existing surface (eyes: open/half/blink/happy)."""
    # Tail
    tail_y = (17 if tail_up else 19) + y_off
    px(surf, 4 + x_off, tail_y, 5, 3, OUTLINE)
    px(surf, 5 + x_off, tail_y + 1, 3, 1, LIGHT)
    px(surf, 3 + x_off, tail_y - 2, 3, 3, OUTLINE)
    px(surf, 4 + x_off, tail_y - 1, 1, 1, EYE)

    # Pointy ears
    px(surf, 10 + x_off, 8 + y_off, 4, 5, OUTLINE)
    px(surf, 11 + x_off, 9 + y_off, 2, 3, LIGHT)
    px(surf, 19 + x_off, 8 + y_off, 4, 5, OUTLINE)
    px(surf, 20 + x_off, 9 + y_off, 2, 3, LIGHT)

    # Main head/body silhouette
    px(surf, 9 + x_off, 12 + y_off, 15, 13, OUTLINE)
    px(surf, 10 + x_off, 13 + y_off, 13, 11, BODY)
    px(surf, 11 + x_off, 13 + y_off, 11, 2, LIGHT)
    px(surf, 13 + x_off, 20 + y_off, 8, 4, BELLY)

    # Eyes
    if eyes == "blink":
        px(surf, 14 + x_off, 17 + y_off, 3, 1, OUTLINE)
        px(surf, 20 + x_off, 17 + y_off, 2, 1, OUTLINE)
    elif eyes == "half":
        # Drowsy half-closed eyelids
        px(surf, 14 + x_off, 16 + y_off, 2, 1, OUTLINE)
        px(surf, 14 + x_off, 17 + y_off, 2, 2, EYE)
        px(surf, 20 + x_off, 16 + y_off, 2, 1, OUTLINE)
        px(surf, 20 + x_off, 17 + y_off, 2, 2, EYE)
    elif eyes == "happy":
        px(surf, 14 + x_off, 16 + y_off, 3, 1, EYE)
        px(surf, 13 + x_off, 17 + y_off, 1, 1, EYE)
        px(surf, 17 + x_off, 17 + y_off, 1, 1, EYE)
        px(surf, 19 + x_off, 16 + y_off, 3, 1, EYE)
        px(surf, 19 + x_off, 17 + y_off, 1, 1, EYE)
        px(surf, 22 + x_off, 17 + y_off, 1, 1, EYE)
    else:
        px(surf, 14 + x_off, 16 + y_off, 2, 3, EYE)
        px(surf, 20 + x_off, 16 + y_off, 2, 3, EYE)

    # Cheeks
    px(surf, 12 + x_off, 19 + y_off, 2, 1, CHEEK)
    px(surf, 21 + x_off, 19 + y_off, 2, 1, CHEEK)

    # Mouth
    if mouth_open:
        px(surf, 18 + x_off, 19 + y_off, 3, 3, OUTLINE)
        px(surf, 19 + x_off, 20 + y_off, 1, 1, CHEEK)
    else:
        px(surf, 18 + x_off, 19 + y_off, 2, 1, OUTLINE)

    # Paws
    left_foot_y = 25 + y_off - (1 if leg_phase == 1 else 0)
    right_foot_y = 25 + y_off - (1 if leg_phase == 2 else 0)
    px(surf, 10 + x_off, left_foot_y, 4, 3, OUTLINE)
    px(surf, 11 + x_off, left_foot_y, 2, 2, LIGHT)
    px(surf, 19 + x_off, right_foot_y, 4, 3, OUTLINE)
    px(surf, 20 + x_off, right_foot_y, 2, 2, LIGHT)


def draw_sparkkit(
    x_off: int = 0,
    y_off: int = 0,
    eyes: str = "open",
    mouth_open: bool = False,
    leg_phase: int = 0,
    tail_up: bool = False,
) -> pygame.Surface:
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_sparkkit_on(surf, x_off, y_off, eyes, mouth_open, leg_phase, tail_up)
    return surf


def draw_sparkkit_sleeping(
    breathe_up: bool = False,
    mouth_puff: bool = False,
    eyes_half: bool = False,
    ear_perk: bool = False,
) -> pygame.Surface:
    """Draws Sparkkit curled up inside the cozy pet bed."""
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    b = -1 if breathe_up else 0
    ear_y = 12 if ear_perk else 13

    draw_bed_back(surf)

    # Curled-up body laying down horizontally
    px(surf, 6, 17 + b, 13, 8, OUTLINE)
    px(surf, 7, 18 + b, 11, 6, BODY)
    px(surf, 8, 18 + b, 9, 2, LIGHT)

    # Tail tucked snugly
    px(surf, 4, 20, 4, 4, OUTLINE)
    px(surf, 5, 21, 2, 2, LIGHT)
    px(surf, 4, 19, 2, 2, EYE)

    # Head resting on pillow
    px(surf, 17, ear_y, 3, 3, OUTLINE)
    px(surf, 18, ear_y + 1, 1, 2, LIGHT)
    px(surf, 22, ear_y, 3, 3, OUTLINE)
    px(surf, 23, ear_y + 1, 1, 2, LIGHT)

    px(surf, 16, 15, 10, 8, OUTLINE)
    px(surf, 17, 16, 8, 6, BODY)
    px(surf, 18, 16, 6, 1, LIGHT)

    # Eyes (closed or half-open for smooth transitions)
    if eyes_half:
        px(surf, 18, 18, 2, 1, OUTLINE)
        px(surf, 18, 19, 2, 1, EYE)
        px(surf, 22, 18, 2, 1, OUTLINE)
        px(surf, 22, 19, 2, 1, EYE)
    else:
        px(surf, 18, 19, 2, 1, OUTLINE)
        px(surf, 22, 19, 2, 1, OUTLINE)

    # Blush & breathing mouth
    px(surf, 17, 20, 1, 1, CHEEK)
    px(surf, 24, 20, 1, 1, CHEEK)
    if mouth_puff:
        px(surf, 20, 20, 2, 2, OUTLINE)
        px(surf, 20, 20, 1, 1, CHEEK)
    else:
        px(surf, 20, 21, 2, 1, OUTLINE)

    # Front rim + tucked paw
    draw_bed_front(surf)
    px(surf, 13, 23, 4, 3, OUTLINE)
    px(surf, 14, 24, 2, 1, LIGHT)

    return surf


def draw_bowl(surf: pygame.Surface, fill_level: int) -> None:
    if fill_level == 2:
        px(surf, 23, 20, 6, 3, FOOD_DARK)
        px(surf, 24, 19, 4, 3, FOOD_GOLD)
        px(surf, 25, 19, 2, 1, SPARKLE)
    elif fill_level == 1:
        px(surf, 24, 21, 4, 2, FOOD_GOLD)
        px(surf, 25, 22, 2, 1, FOOD_DARK)

    px(surf, 21, 22, 10, 6, OUTLINE)
    px(surf, 22, 23, 8, 1, BOWL_RIM)
    px(surf, 22, 24, 8, 3, BOWL_MAIN)


def draw_ball(surf: pygame.Surface, x: int, y: int) -> None:
    px(surf, x + 1, y, 3, 5, OUTLINE)
    px(surf, x, y + 1, 5, 3, OUTLINE)
    px(surf, x + 1, y + 1, 3, 3, BALL_CYAN)
    px(surf, x + 1, y + 1, 1, 1, BALL_LIGHT)
    px(surf, x + 2, y + 2, 2, 1, BALL_GOLD)


def draw_star_treat(surf: pygame.Surface, x: int, y: int) -> None:
    px(surf, x + 2, y, 1, 5, TREAT_GLOW)
    px(surf, x, y + 2, 5, 1, TREAT_GLOW)
    px(surf, x + 1, y + 1, 3, 3, TREAT_PINK)
    px(surf, x + 2, y + 2, 1, 1, SPARKLE)


def save_strip(filename: str, frames: list[pygame.Surface]) -> None:
    strip = pygame.Surface((CELL * len(frames), CELL), pygame.SRCALPHA)
    for idx, frame in enumerate(frames):
        strip.blit(frame, (idx * CELL, 0))
    pygame.image.save(strip, str(OUT_DIR / filename))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 0. Empty Pet Bed prop (always sits in the room corner)
    empty_bed = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(empty_bed)
    draw_bed_front(empty_bed)
    save_strip("bed.png", [empty_bed])

    # 1. Idle (gentle breathing + blink)
    idle_frames = [
        draw_sparkkit(y_off=0, tail_up=False),
        draw_sparkkit(y_off=1, tail_up=True),
        draw_sparkkit(y_off=0, tail_up=False),
        draw_sparkkit(y_off=0, eyes="blink", tail_up=False),
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

    # 3. Sleep Start (6-frame yawn -> crouch -> hop into bed -> settle -> curl up)
    sleep_start_frames = []

    # Frame 0: Standing beside bed, sleepy yawn
    s0 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(s0)
    draw_bed_front(s0)
    draw_sparkkit_on(s0, x_off=-3, y_off=0, eyes="half", mouth_open=True, tail_up=False)
    sleep_start_frames.append(s0)

    # Frame 1: Crouch to hop in
    s1 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(s1)
    draw_bed_front(s1)
    draw_sparkkit_on(s1, x_off=-2, y_off=2, eyes="half", tail_up=False)
    sleep_start_frames.append(s1)

    # Frame 2: Hop over bed rim
    s2 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(s2)
    draw_bed_front(s2)
    draw_sparkkit_on(s2, x_off=-1, y_off=-4, eyes="half", tail_up=True)
    sleep_start_frames.append(s2)

    # Frame 3: Land inside bed cushion (tucked behind front rim)
    s3 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(s3)
    draw_sparkkit_on(s3, x_off=0, y_off=2, eyes="half", tail_up=False)
    draw_bed_front(s3)
    sleep_start_frames.append(s3)

    # Frame 4: Curl horizontally onto pillow, eyes still half-shut
    sleep_start_frames.append(draw_sparkkit_sleeping(breathe_up=True, eyes_half=True))

    # Frame 5: Eyes fully shut (matches Frame 0 of sleep.png seamlessly)
    sleep_start_frames.append(draw_sparkkit_sleeping(breathe_up=False, eyes_half=False))
    save_strip("sleep_start.png", sleep_start_frames)

    # 4. Sleep Loop (calm breathing in bed)
    sleep_frames = [
        draw_sparkkit_sleeping(breathe_up=False, mouth_puff=False),
        draw_sparkkit_sleeping(breathe_up=True, mouth_puff=False),
        draw_sparkkit_sleeping(breathe_up=True, mouth_puff=True),
        draw_sparkkit_sleeping(breathe_up=False, mouth_puff=False),
    ]
    save_strip("sleep.png", sleep_frames)

    # 5. Wake Up (6-frame ear twitch -> blink open -> morning stretch -> hop out)
    wake_up_frames = [
        draw_sparkkit_sleeping(breathe_up=True, eyes_half=False, ear_perk=True),
        draw_sparkkit_sleeping(breathe_up=False, eyes_half=True, ear_perk=True),
    ]

    # Frame 2: Big morning stretch & yawn inside bed
    w2 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(w2)
    draw_sparkkit_on(w2, x_off=0, y_off=0, eyes="happy", mouth_open=True, tail_up=True)
    draw_bed_front(w2)
    px(w2, 7, 5, 2, 2, SPARKLE)
    px(w2, 24, 6, 2, 2, SPARKLE)
    wake_up_frames.append(w2)

    # Frame 3: Wide awake in bed, ready to jump out
    w3 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(w3)
    draw_sparkkit_on(w3, x_off=0, y_off=1, eyes="open", tail_up=True)
    draw_bed_front(w3)
    wake_up_frames.append(w3)

    # Frame 4: Hop up and out of bed
    w4 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(w4)
    draw_bed_front(w4)
    draw_sparkkit_on(w4, x_off=-2, y_off=-4, eyes="open", tail_up=True)
    wake_up_frames.append(w4)

    # Frame 5: Land on floor beside bed (matches WALK_TO_BED_X seamlessly)
    w5 = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    draw_bed_back(w5)
    draw_bed_front(w5)
    draw_sparkkit_on(w5, x_off=-3, y_off=0, eyes="happy", tail_up=True)
    wake_up_frames.append(w5)
    save_strip("wake_up.png", wake_up_frames)

    # 6. Eat Meal (6-frame food bowl chomp with flying crumbs)
    eat_frames = []
    specs = [
        (-3, 0, False, "open",  2, False),
        (-1, 2, True,  "open",  2, False),
        (-2, 1, False, "open",  1, True),
        (-1, 2, True,  "open",  1, False),
        (-2, 0, False, "happy", 0, True),
        (-3, -1, False, "happy", 0, False),
    ]
    for x_off, y_off, mouth, eye_mode, fill, crumbs in specs:
        f = draw_sparkkit(x_off=x_off, y_off=y_off, eyes=eye_mode, mouth_open=mouth, tail_up=(eye_mode == "happy"))
        draw_bowl(f, fill)
        if crumbs:
            px(f, 20, 17, 2, 2, FOOD_GOLD)
            px(f, 24, 15, 1, 1, FOOD_GOLD)
            px(f, 27, 17, 1, 1, SPARKLE)
        if fill == 0 and eye_mode == "happy":
            px(f, 25, 17, 2, 2, SPARKLE)
        eat_frames.append(f)
    save_strip("eat.png", eat_frames)

    # 7. Snack / Treat (6-frame star-treat toss & mid-air catch)
    snack_frames = []
    f0 = draw_sparkkit(x_off=-2, y_off=0, tail_up=True)
    draw_star_treat(f0, 24, 2)
    snack_frames.append(f0)

    f1 = draw_sparkkit(x_off=-1, y_off=1, mouth_open=True, tail_up=True)
    draw_star_treat(f1, 22, 8)
    snack_frames.append(f1)

    f2 = draw_sparkkit(x_off=0, y_off=-3, mouth_open=True, tail_up=True)
    draw_star_treat(f2, 21, 13)
    snack_frames.append(f2)

    f3 = draw_sparkkit(x_off=0, y_off=-2, eyes="happy", tail_up=True)
    px(f3, 24, 10, 2, 2, SPARKLE)
    px(f3, 12, 5, 2, 2, TREAT_PINK)
    snack_frames.append(f3)

    f4 = draw_sparkkit(x_off=-1, y_off=0, eyes="happy", mouth_open=True, tail_up=True)
    px(f4, 26, 13, 2, 2, TREAT_GLOW)
    snack_frames.append(f4)

    f5 = draw_sparkkit(x_off=-2, y_off=-1, eyes="happy", tail_up=True)
    px(f5, 7, 5, 2, 2, SPARKLE)
    px(f5, 24, 6, 2, 2, SPARKLE)
    snack_frames.append(f5)
    save_strip("snack.png", snack_frames)

    # 8. Play (6-frame bouncing ball chase & mid-air boop)
    play_frames = []
    p0 = draw_sparkkit(x_off=-3, y_off=1, tail_up=True)
    draw_ball(p0, 24, 22)
    play_frames.append(p0)

    p1 = draw_sparkkit(x_off=-1, y_off=0, leg_phase=1, tail_up=True)
    draw_ball(p1, 24, 13)
    play_frames.append(p1)

    p2 = draw_sparkkit(x_off=-1, y_off=-1, eyes="happy", tail_up=True)
    draw_ball(p2, 19, 4)
    play_frames.append(p2)

    p3 = draw_sparkkit(x_off=0, y_off=-4, mouth_open=True, tail_up=True)
    draw_ball(p3, 22, 2)
    px(p3, 20, 8, 2, 2, SPARKLE)
    play_frames.append(p3)

    p4 = draw_sparkkit(x_off=-2, y_off=0, eyes="happy", leg_phase=2, tail_up=False)
    draw_ball(p4, 26, 15)
    play_frames.append(p4)

    p5 = draw_sparkkit(x_off=-3, y_off=-2, eyes="happy", tail_up=True)
    draw_ball(p5, 25, 22)
    px(p5, 8, 4, 2, 2, SPARKLE)
    play_frames.append(p5)
    save_strip("play.png", play_frames)

    # 9. Happy (4-frame hop + sparkles)
    happy_frames = []
    for i in range(4):
        hop = -4 if i in (1, 2) else 0
        f = draw_sparkkit(y_off=hop, eyes="happy", mouth_open=(i in (1, 2)), tail_up=True)
        if i in (1, 2):
            px(f, 6, 4 + i, 2, 2, SPARKLE)
            px(f, 25, 6 - i, 2, 2, SPARKLE)
            px(f, 16, 2, 2, 2, SPARKLE)
        happy_frames.append(f)
    save_strip("happy.png", happy_frames)

    print(f"Generated 10 sprite assets in: {OUT_DIR}")


if __name__ == "__main__":
    main()