"""Home room scene for Z-Pet (icon action dock, bedtime routine, decorated room, clock window)."""

from datetime import datetime
import math
import random
import pygame

import settings
from core import sound
from core.animator import load_species_animations
from core.display import KEYS_LEFT, KEYS_RIGHT
from core.pet import Pet
from core.save_manager import save_pet

# Stat bar & UI colors
BAR_BG = (52, 42, 74)
BAR_GOOD = (105, 225, 145)
BAR_WARN = (245, 195, 85)
BAR_LOW = (240, 95, 115)
HEART_COLOR = (255, 105, 165)
DOCK_SLOT_BG = (34, 24, 54)
DOCK_SLOT_SEL = (84, 56, 136)
DOCK_SLOT_BORDER = (68, 50, 104)

# Permanent pet bed placement in the right corner of the room
BED_X = 240
WALK_TO_BED_X = BED_X - 6

SKY_PRESET_HOURS = {
    "dawn": 6.0,
    "day": 12.0,
    "sunset": 18.5,
    "night": 22.0,
}

# 8 bottom-dock actions navigated with ←/→ and triggered with Enter/Space
HOME_ACTIONS = [
    ("feed",   "Meal"),
    ("treat",  "Treat"),
    ("play",   "Play"),
    ("train",  "Train"),
    ("battle", "Battle"),
    ("clean",  "Clean"),
    ("sleep",  "Bed"),
    ("hug",    "Hug"),
    ("status", "Status"),
]


def build_action_icons() -> dict[str, pygame.Surface]:
    """Pre-renders crisp 14x14 pixel-art icons for the bottom dock."""
    icons: dict[str, pygame.Surface] = {}
    out = (26, 16, 40, 255)

    # 1. Meal (red apple with leaf)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.rect(s, (160, 106, 68, 255), (6, 1, 2, 3))
    pygame.draw.rect(s, (105, 225, 145, 255), (8, 1, 3, 2))
    pygame.draw.rect(s, out, (2, 4, 10, 8))
    pygame.draw.rect(s, out, (3, 3, 8, 10))
    pygame.draw.rect(s, (235, 78, 98, 255), (3, 4, 8, 8))
    pygame.draw.rect(s, (235, 78, 98, 255), (2, 5, 10, 6))
    s.set_at((6, 4), out)
    s.set_at((7, 4), out)
    pygame.draw.rect(s, (255, 178, 188, 255), (4, 5, 2, 2))
    icons["feed"] = s

    # 2. Treat (golden star candy)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    gold = (255, 212, 82, 255)
    hi = (255, 248, 188, 255)
    pygame.draw.rect(s, gold, (6, 1, 2, 12))
    pygame.draw.rect(s, gold, (1, 6, 12, 2))
    pygame.draw.rect(s, gold, (3, 5, 8, 4))
    pygame.draw.rect(s, gold, (5, 3, 4, 8))
    pygame.draw.rect(s, gold, (4, 4, 6, 6))
    pygame.draw.rect(s, hi, (5, 5, 4, 4))
    pygame.draw.rect(s, (255, 255, 255, 255), (6, 6, 2, 2))
    icons["treat"] = s

    # 3. Play (striped bouncy ball)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.circle(s, out, (7, 7), 6)
    pygame.draw.circle(s, (242, 92, 142, 255), (7, 7), 5)
    pygame.draw.line(s, (255, 224, 112, 255), (3, 7), (11, 7), 2)
    pygame.draw.rect(s, (255, 206, 224, 255), (4, 4, 2, 2))
    icons["play"] = s

    # 4. Train (dumbbell)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.rect(s, out, (0, 4, 14, 6))
    pygame.draw.rect(s, (206, 214, 236, 255), (4, 6, 6, 2))
    pygame.draw.rect(s, (110, 185, 245, 255), (3, 3, 2, 8))
    pygame.draw.rect(s, (110, 185, 245, 255), (9, 3, 2, 8))
    pygame.draw.rect(s, (78, 142, 215, 255), (1, 5, 2, 4))
    pygame.draw.rect(s, (78, 142, 215, 255), (11, 5, 2, 4))
    s.set_at((3, 4), (220, 242, 255, 255))
    s.set_at((9, 4), (220, 242, 255, 255))
    icons["train"] = s

    # 5. Clean (glossy soap bubbles + sparkle)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.circle(s, (115, 218, 255, 255), (5, 8), 4)
    pygame.draw.circle(s, (66, 152, 212, 255), (5, 8), 3)
    pygame.draw.rect(s, (240, 250, 255, 255), (3, 6, 2, 2))
    pygame.draw.circle(s, (150, 232, 255, 255), (10, 4), 2)
    s.set_at((9, 3), (255, 255, 255, 255))
    pygame.draw.line(s, (255, 240, 140, 255), (11, 9), (11, 12), 1)
    pygame.draw.line(s, (255, 240, 140, 255), (10, 10), (12, 10), 1)
    icons["clean"] = s

    # 6a. Sleep (crescent moon)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 232, 128, 255), (7, 7), 5)
    pygame.draw.circle(s, (0, 0, 0, 0), (10, 5), 4)
    s.set_at((11, 3), (235, 225, 255, 255))
    s.set_at((12, 7), (200, 185, 245, 255))
    icons["sleep"] = s

    # 6b. Wake (bright sun)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    sun = (255, 218, 92, 255)
    pygame.draw.circle(s, sun, (7, 7), 3)
    pygame.draw.rect(s, (255, 248, 196, 255), (6, 6, 2, 2))
    for rx, ry, rw, rh in ((6, 1, 2, 2), (6, 11, 2, 2), (1, 6, 2, 2), (11, 6, 2, 2)):
        pygame.draw.rect(s, sun, (rx, ry, rw, rh))
    for px, py in ((3, 3), (10, 3), (3, 10), (10, 10)):
        s.set_at((px, py), sun)
    icons["wake"] = s

    # 7. Hug (pixel heart)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    heart_rows = [
        "..###..###..",
        ".##########.",
        ".##########.",
        ".##########.",
        "..########..",
        "...######...",
        "....####....",
        ".....##.....",
    ]
    for r, row in enumerate(heart_rows):
        for c, ch in enumerate(row):
            if ch == "#":
                s.set_at((1 + c, 3 + r), (255, 96, 158, 255))
    pygame.draw.rect(s, (255, 192, 218, 255), (3, 4, 2, 2))
    icons["hug"] = s

    # 8. Status (mini colored stat-bar chart)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    pygame.draw.rect(s, (208, 198, 232, 255), (2, 2, 1, 10))
    pygame.draw.rect(s, (208, 198, 232, 255), (2, 11, 10, 1))
    pygame.draw.rect(s, (240, 110, 125, 255), (4, 7, 2, 4))
    pygame.draw.rect(s, (110, 185, 245, 255), (7, 4, 2, 7))
    pygame.draw.rect(s, (105, 225, 145, 255), (10, 2, 2, 9))
    icons["status"] = s

    # 9. Battle (crossed silver swords with gold hilts)
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    blade = (224, 232, 248, 255)
    hilt = (255, 212, 82, 255)
    pygame.draw.line(s, blade, (2, 2), (10, 10), 2)
    pygame.draw.line(s, blade, (11, 2), (3, 10), 2)
    pygame.draw.line(s, hilt, (2, 8), (5, 11), 2)
    pygame.draw.line(s, hilt, (11, 8), (8, 11), 2)
    pygame.draw.rect(s, (196, 86, 112, 255), (1, 10, 2, 2))
    pygame.draw.rect(s, (196, 86, 112, 255), (10, 10, 2, 2))
    icons["battle"] = s

    return icons


def load_bed_sprite(species_dir) -> pygame.Surface:
    bed_path = species_dir / "bed.png"
    img = pygame.image.load(str(bed_path)).convert_alpha()
    size = settings.SPRITE_SIZE * settings.SPRITE_SCALE
    return pygame.transform.scale(img, (size, size))


def load_poop_sprite() -> pygame.Surface:
    custom_path = settings.ASSETS_DIR / "ui" / "poop.png"
    if custom_path.exists():
        img = pygame.image.load(str(custom_path)).convert_alpha()
        return pygame.transform.scale(img, (16, 16))

    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    outline = (30, 18, 12, 255)
    brown = (128, 78, 42, 255)
    highlight = (166, 112, 68, 255)

    pygame.draw.rect(surf, outline, (2, 10, 12, 5))
    pygame.draw.rect(surf, brown, (3, 11, 10, 3))
    pygame.draw.rect(surf, outline, (4, 7, 8, 4))
    pygame.draw.rect(surf, brown, (5, 8, 6, 3))
    pygame.draw.rect(surf, highlight, (5, 8, 2, 1))
    pygame.draw.rect(surf, outline, (6, 4, 4, 4))
    pygame.draw.rect(surf, brown, (7, 5, 2, 3))
    pygame.draw.rect(surf, highlight, (7, 5, 1, 1))
    return surf


def draw_pixel_heart(surf: pygame.Surface, x: int, y: int, color: tuple = HEART_COLOR) -> None:
    pattern = [
        ".##.##.",
        "#######",
        "#######",
        ".#####.",
        "..###..",
        "...#...",
    ]
    for r, row in enumerate(pattern):
        for c, ch in enumerate(row):
            if ch == "#":
                surf.set_at((x + c, y + r), color)


def draw_room_decorations(
    canvas: pygame.Surface,
    pet: Pet,
    lamp_dim: float,
    elapsed: float,
) -> None:
    """Draws cozy pixel-art bedroom wallpaper, shelf, poster, plant, lamp, and rug."""
    canvas.fill(settings.COLOR_BG)
    stripe_col = (34, 24, 54)
    for sx in range(0, settings.LOGICAL_WIDTH, 16):
        pygame.draw.rect(canvas, stripe_col, (sx, 38, 6, 84))

    pygame.draw.rect(canvas, (54, 38, 82), (0, 121, settings.LOGICAL_WIDTH, 5))
    pygame.draw.line(canvas, (86, 62, 126), (0, 121), (settings.LOGICAL_WIDTH, 121), 1)

    # Floor + patterned woven rug
    pygame.draw.rect(canvas, settings.COLOR_FLOOR, (0, 126, settings.LOGICAL_WIDTH, 20))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 126), (settings.LOGICAL_WIDTH, 126), 1)
    pygame.draw.ellipse(canvas, (76, 52, 114), (72, 129, 128, 14))
    pygame.draw.ellipse(canvas, (104, 72, 152), (82, 131, 108, 10), 1)
    pygame.draw.ellipse(canvas, (62, 42, 94), (94, 133, 84, 6))

    # Wall shelf with books, succulent, and Star Catch trophy
    shelf_x, shelf_y, shelf_w = 84, 74, 62
    pygame.draw.rect(canvas, (30, 18, 42), (shelf_x + 2, shelf_y + 4, shelf_w, 3))
    pygame.draw.rect(canvas, (112, 74, 58), (shelf_x, shelf_y, shelf_w, 4))
    pygame.draw.rect(canvas, (148, 102, 82), (shelf_x, shelf_y, shelf_w, 1))
    pygame.draw.rect(canvas, (82, 54, 44), (shelf_x + 6, shelf_y + 4, 3, 5))
    pygame.draw.rect(canvas, (82, 54, 44), (shelf_x + shelf_w - 9, shelf_y + 4, 3, 5))

    pygame.draw.rect(canvas, (212, 86, 112), (shelf_x + 4, shelf_y - 10, 4, 10))
    pygame.draw.rect(canvas, (94, 178, 232), (shelf_x + 9, shelf_y - 12, 4, 12))
    pygame.draw.rect(canvas, (238, 194, 88), (shelf_x + 14, shelf_y - 9, 4, 9))

    pygame.draw.rect(canvas, (186, 102, 72), (shelf_x + 27, shelf_y - 6, 8, 6))
    pygame.draw.rect(canvas, (214, 128, 96), (shelf_x + 26, shelf_y - 7, 10, 2))
    pygame.draw.rect(canvas, (82, 188, 112), (shelf_x + 29, shelf_y - 13, 4, 6))
    pygame.draw.rect(canvas, (118, 222, 144), (shelf_x + 30, shelf_y - 12, 2, 4))
    pygame.draw.rect(canvas, (82, 188, 112), (shelf_x + 27, shelf_y - 11, 2, 3))
    pygame.draw.rect(canvas, (82, 188, 112), (shelf_x + 33, shelf_y - 10, 2, 2))

    trophy_col = (255, 214, 86) if pet.high_score > 0 else (126, 116, 152)
    trophy_hi = (255, 246, 185) if pet.high_score > 0 else (168, 158, 192)
    tx = shelf_x + 46
    pygame.draw.rect(canvas, (88, 62, 48), (tx, shelf_y - 2, 10, 2))
    pygame.draw.rect(canvas, trophy_col, (tx + 3, shelf_y - 5, 4, 3))
    pygame.draw.rect(canvas, trophy_col, (tx + 1, shelf_y - 12, 8, 7))
    pygame.draw.rect(canvas, trophy_hi, (tx + 2, shelf_y - 11, 2, 4))
    if pet.high_score > 0 and int(elapsed * 3) % 2 == 0:
        canvas.fill((255, 252, 220), (tx + 9, shelf_y - 14, 2, 2))

    # Framed wall poster
    px_x, px_y, px_w, px_h = 166, 48, 28, 24
    pygame.draw.rect(canvas, (20, 14, 34), (px_x + 2, px_y + 2, px_w, px_h))
    pygame.draw.rect(canvas, (30, 26, 62), (px_x, px_y, px_w, px_h))
    pygame.draw.rect(canvas, settings.COLOR_ACCENT, (px_x, px_y, px_w, px_h), 2)
    pygame.draw.circle(canvas, (238, 134, 188), (px_x + 14, px_y + 12), 5)
    pygame.draw.line(canvas, (255, 228, 136), (px_x + 6, px_y + 14), (px_x + 22, px_y + 10), 1)
    canvas.fill((245, 240, 255), (px_x + 5, px_y + 5, 2, 2))
    canvas.fill((245, 240, 255), (px_x + 21, px_y + 18, 1, 1))

    # Standing floor lamp next to bed
    lamp_x = 223
    lamp_on = lamp_dim < 0.55
    if lamp_on:
        glow = pygame.Surface((46, 46), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 220, 130, 34), (23, 23), 22)
        pygame.draw.circle(glow, (255, 232, 155, 42), (23, 23), 13)
        canvas.blit(glow, (lamp_x - 23, 66))

    pygame.draw.rect(canvas, (76, 62, 102), (lamp_x - 1, 88, 3, 36))
    pygame.draw.rect(canvas, (56, 44, 78), (lamp_x - 7, 122, 15, 4))
    pygame.draw.rect(canvas, (108, 88, 146), (lamp_x - 5, 122, 11, 1))

    shade_pts = [(lamp_x - 6, 76), (lamp_x + 6, 76), (lamp_x + 10, 89), (lamp_x - 10, 89)]
    shade_col = (248, 206, 118) if lamp_on else (112, 86, 148)
    shade_rim = (255, 236, 178) if lamp_on else (78, 58, 110)
    pygame.draw.polygon(canvas, shade_col, shade_pts)
    pygame.draw.polygon(canvas, (34, 22, 52), shade_pts, 1)
    pygame.draw.line(canvas, shade_rim, (lamp_x - 8, 88), (lamp_x + 8, 88), 1)

    # Potted leafy floor plant on left
    pot_x, pot_y = 6, 114
    pygame.draw.rect(canvas, (176, 94, 66), (pot_x + 2, pot_y, 12, 11))
    pygame.draw.rect(canvas, (206, 120, 88), (pot_x, pot_y - 2, 16, 3))
    pygame.draw.rect(canvas, (132, 68, 48), (pot_x + 2, pot_y + 9, 12, 2))
    pygame.draw.ellipse(canvas, (56, 152, 92), (pot_x + 4, pot_y - 16, 8, 15))
    pygame.draw.ellipse(canvas, (82, 192, 116), (pot_x - 1, pot_y - 12, 8, 10))
    pygame.draw.ellipse(canvas, (82, 192, 116), (pot_x + 9, pot_y - 13, 8, 10))
    pygame.draw.ellipse(canvas, (118, 224, 144), (pot_x + 6, pot_y - 14, 4, 8))


def draw_clock_window(canvas: pygame.Surface, hour_float: float, elapsed: float) -> None:
    wx, wy, ww, wh = 18, 44, 44, 28
    win_rect = pygame.Rect(wx, wy, ww, wh)

    pygame.draw.rect(canvas, (132, 96, 186), (wx - 7, wy - 3, ww + 14, 2))
    pygame.draw.rect(canvas, (98, 64, 148), (wx - 6, wy - 1, 6, wh + 3))
    pygame.draw.rect(canvas, (124, 86, 180), (wx - 5, wy - 1, 2, wh + 2))
    pygame.draw.rect(canvas, (98, 64, 148), (wx + ww, wy - 1, 6, wh + 3))
    pygame.draw.rect(canvas, (124, 86, 180), (wx + ww + 3, wy - 1, 2, wh + 2))

    canvas.set_clip(win_rect)

    if 5.0 <= hour_float < 7.5:
        t = (hour_float - 5.0) / 2.5
        pygame.draw.rect(canvas, (76, 70, 138), (wx, wy, ww, 15))
        pygame.draw.rect(canvas, (238, 152, 128), (wx, wy + 15, ww, 13))
        sun_x = wx + 8 + int(t * 8)
        sun_y = wy + 24 - int(t * 10)
        pygame.draw.circle(canvas, (255, 214, 120), (sun_x, sun_y), 4)

    elif 7.5 <= hour_float < 17.5:
        t = (hour_float - 7.5) / 10.0
        pygame.draw.rect(canvas, (74, 144, 216), (wx, wy, ww, 17))
        pygame.draw.rect(canvas, (124, 186, 236), (wx, wy + 17, ww, 11))

        sun_x = wx + 6 + int(t * (ww - 12))
        sun_y = wy + 17 - int(math.sin(t * math.pi) * 10)
        pygame.draw.circle(canvas, (255, 232, 112), (sun_x, sun_y), 4)

        cloud_x = wx - 12 + int((elapsed * 3.5) % (ww + 16))
        pygame.draw.rect(canvas, (242, 246, 255), (cloud_x, wy + 16, 12, 4))
        pygame.draw.rect(canvas, (242, 246, 255), (cloud_x + 3, wy + 13, 6, 3))

    elif 17.5 <= hour_float < 20.0:
        t = (hour_float - 17.5) / 2.5
        pygame.draw.rect(canvas, (52, 38, 102), (wx, wy, ww, 14))
        pygame.draw.rect(canvas, (226, 108, 92), (wx, wy + 14, ww, 14))
        sun_x = wx + 28 + int(t * 8)
        sun_y = wy + 13 + int(t * 12)
        pygame.draw.circle(canvas, (255, 172, 92), (sun_x, sun_y), 4)
        if t > 0.45:
            canvas.fill((240, 240, 255), (wx + 9, wy + 6, 1, 1))

    else:
        night_h = (hour_float - 20.0) % 24.0
        t = min(1.0, night_h / 9.0)
        sky = (14, 18, 46)
        pygame.draw.rect(canvas, sky, win_rect)

        moon_x = wx + 7 + int(t * (ww - 14))
        moon_y = wy + 16 - int(math.sin(t * math.pi) * 8)
        pygame.draw.circle(canvas, (255, 242, 175), (moon_x, moon_y), 4)
        pygame.draw.circle(canvas, sky, (moon_x + 2, moon_y - 1), 3)

        twinkle = int(elapsed * 2) % 2 == 0
        s1 = (245, 245, 255) if twinkle else (140, 148, 200)
        s2 = (140, 148, 200) if twinkle else (245, 245, 255)
        canvas.fill(s1, (wx + 7, wy + 7, 2, 2))
        canvas.fill(s2, (wx + 24, wy + 19, 1, 1))
        canvas.fill(s1, (wx + 35, wy + 8, 1, 1))
        canvas.fill(s2, (wx + 13, wy + 21, 1, 1))

    canvas.set_clip(None)

    frame_col = settings.COLOR_ACCENT
    pygame.draw.rect(canvas, frame_col, win_rect, 2)
    pygame.draw.line(canvas, frame_col, (wx + ww // 2, wy), (wx + ww // 2, wy + wh - 1), 1)
    pygame.draw.line(canvas, frame_col, (wx, wy + wh // 2), (wx + ww - 1, wy + wh // 2), 1)
    pygame.draw.rect(canvas, (112, 74, 58), (wx - 5, wy + wh, ww + 10, 3))
    pygame.draw.rect(canvas, (148, 102, 82), (wx - 5, wy + wh, ww + 10, 1))


def draw_thought_bubble(canvas: pygame.Surface, x: int, y: int, need: str) -> None:
    bx = max(6, min(settings.LOGICAL_WIDTH - 28, x))
    by = max(42, y)

    pygame.draw.rect(canvas, (245, 240, 255), (bx, by, 20, 15), border_radius=4)
    pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bx, by, 20, 15), 1, border_radius=4)
    pygame.draw.rect(canvas, (245, 240, 255), (bx + 4, by + 16, 3, 3))
    pygame.draw.rect(canvas, (245, 240, 255), (bx + 1, by + 20, 2, 2))

    if need == "hunger":
        pygame.draw.rect(canvas, (215, 85, 85), (bx + 5, by + 4, 8, 6))
        pygame.draw.rect(canvas, (240, 215, 195), (bx + 13, by + 6, 3, 2))
    elif need == "clean":
        pygame.draw.rect(canvas, (132, 82, 44), (bx + 6, by + 9, 8, 3))
        pygame.draw.rect(canvas, (132, 82, 44), (bx + 8, by + 6, 4, 3))
        pygame.draw.rect(canvas, (132, 82, 44), (bx + 9, by + 4, 2, 2))
    elif need == "energy":
        pygame.draw.circle(canvas, (110, 90, 200), (bx + 10, by + 7), 4)
        pygame.draw.circle(canvas, (245, 240, 255), (bx + 12, by + 6), 3)
    elif need == "happy":
        canvas.fill((70, 50, 110), (bx + 6, by + 5, 2, 2))
        canvas.fill((70, 50, 110), (bx + 12, by + 5, 2, 2))
        pygame.draw.rect(canvas, (70, 50, 110), (bx + 7, by + 10, 6, 1))


def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    hours, rem_mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {rem_mins}m"
    return f"{rem_mins}m"


def draw_stat_bar(
    canvas: pygame.Surface,
    font_mono: pygame.font.Font,
    x: int,
    y: int,
    slot_w: int,
    label: str,
    value: float,
) -> None:
    lbl = font_mono.render(label, True, settings.COLOR_MUTED)
    canvas.blit(lbl, (x, y))

    bar_x = x + lbl.get_width() + 2
    bar_y = y + 3
    bar_w = max(32, slot_w - lbl.get_width() - 5)
    bar_h = 8
    pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h))

    if value >= 60:
        fill_color = BAR_GOOD
    elif value >= 30:
        fill_color = BAR_WARN
    else:
        fill_color = BAR_LOW

    fill_w = int((max(0.0, min(100.0, value)) / 100.0) * bar_w)
    if fill_w > 0:
        pygame.draw.rect(canvas, fill_color, (bar_x, bar_y, fill_w, bar_h))
    pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 1)


class HomeScene:
    """Main virtual pet bedroom scene with icon-driven bottom action dock."""

    accepts_text_input = False

    def __init__(
        self,
        fonts: dict,
        config: dict,
        pet: Pet,
        offline_seconds: float = 0.0,
        is_new: bool = False,
        return_toast: str = "",
        return_anim: str | None = None,
    ):
        self.fonts = fonts
        self.config = config
        self.pet = pet

        self._load_pet_assets()
        self.poop_sprite = load_poop_sprite()
        self.icons = build_action_icons()
        self.dim_overlay = pygame.Surface((settings.LOGICAL_WIDTH, 108), pygame.SRCALPHA)

        self.rendered_size = settings.SPRITE_SIZE * settings.SPRITE_SCALE
        self.pet_y = 128 - self.rendered_size
        self.walk_speed = 38.0 * self.pet.personality["walk_speed_mult"]
        self.bed_walk_speed = 62.0
        self.wander_timer = 0.8

        # Bottom icon dock selection state
        self.action_idx = 0
        self.label_timer = 2.0

        if pet.alive and pet.sleeping:
            self.bed_state = "sleeping"
            self.pet_x = float(WALK_TO_BED_X)
            self.target_x = self.pet_x
            self.lamp_dim = 1.0
            self.animator.facing_left = False
            self.animator.play("sleep", restart=True)
        else:
            self.bed_state = "awake"
            self.pet_x = 112.0
            self.target_x = self._pick_new_target(112.0)
            self.lamp_dim = 0.0

        self.toast_msg = ""
        self.toast_timer = 0.0
        self.autosave_timer = 0.0
        self.elapsed = 0.0
        self.hearts: list[dict] = []

        if pet.alive and pet.sleeping:
         self.bed_state = "sleeping"
         self.pet_x = float(WALK_TO_BED_X)
         self.target_x = self.pet_x
         self.lamp_dim = 1.0
         self.animator.facing_left = False
         self.animator.play("sleep", restart=True)
        else:
         self.bed_state = "awake"
         self.pet_x = 112.0
         self.target_x = self._pick_new_target(112.0)
         self.lamp_dim = 0.0
         
        if is_new:
            self.animator.play("happy", restart=True, next_anim="idle")
            self.spawn_hearts(4)
            self.show_toast(f"{pet.name} hatched!", duration=2.6)
        elif return_toast:
            if return_anim and self.bed_state == "awake":
                self.animator.facing_left = False
                self.animator.play(return_anim, restart=True, next_anim="idle")
                if return_anim in ("happy", "play"):
                    self.spawn_hearts(3)
            self.show_toast(return_toast, duration=2.6)
        elif offline_seconds >= 60:
            self.show_toast(f"Welcome back! Away {format_duration(offline_seconds)}", duration=3.5)

    def _load_pet_assets(self) -> None:
        sprite_dir = settings.SPRITES_DIR / self.pet.species_id
        self.animator = load_species_animations(
            sprite_dir,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=self.pet.color,
        )
        self.bed_sprite = load_bed_sprite(sprite_dir)

    def _pick_new_target(self, current_x: float) -> float:
        min_x = 24
        max_x = BED_X - self.rendered_size - 16
        for _ in range(8):
            candidate = float(random.randint(min_x, max_x))
            if abs(candidate - current_x) >= 28.0:
                return candidate
        return float(min_x if current_x > (min_x + max_x) / 2 else max_x)

    def show_toast(self, message: str, duration: float = 2.2) -> None:
        self.toast_msg = message
        self.toast_timer = duration

    def spawn_hearts(self, count: int = 3) -> None:
        for _ in range(count):
            self.hearts.append({
                "x": self.pet_x + random.uniform(14, 46),
                "y": self.pet_y + random.uniform(10, 22),
                "vy": random.uniform(16.0, 26.0),
                "life": random.uniform(0.9, 1.4),
            })

    def _get_clock_info(self) -> tuple[float, str]:
        now = datetime.now()
        hh, mm = now.hour, now.minute

        sky_mode = self.config.get("sky_mode", "auto")
        if sky_mode in SKY_PRESET_HOURS:
            hour_float = SKY_PRESET_HOURS[sky_mode]
        else:
            hour_float = hh + mm / 60.0

        if self.config.get("clock_24h", False):
            clock_str = f"{hh:02d}:{mm:02d}"
        else:
            period = "AM" if hh < 12 else "PM"
            hour_12 = hh % 12 or 12
            clock_str = f"{hour_12}:{mm:02d}{period}"
        return hour_float, clock_str

    def _action_needs_alert(self, action_id: str) -> bool:
        if not self.pet.alive:
            return False
        if action_id == "feed":
            return self.pet.hunger < 35.0
        if action_id == "clean":
            return len(self.pet.poops) > 0 or self.pet.clean < 40.0
        if action_id == "sleep":
            return (not self.pet.sleeping) and self.pet.energy < 30.0
        if action_id == "play":
            return (not self.pet.sleeping) and self.pet.happy < 35.0
        return False

    def _activate_selected_action(self) -> tuple[str, dict] | None:
        action_id = HOME_ACTIONS[self.action_idx][0]

        if action_id == "status":
            sound.play("select")
            save_pet(self.pet)
            return ("status", {"pet": self.pet})

        if action_id == "sleep":
            ok, msg = self.pet.toggle_sleep()
            if ok:
                sound.play("sleep" if self.pet.sleeping else "wake")
                if self.pet.sleeping:
                    self.bed_state = "walking_to_bed"
                else:
                    if self.bed_state in ("tucking_in", "sleeping"):
                        self.bed_state = "waking_up"
                        self.animator.facing_left = False
                        self.animator.play("wake_up", restart=True, next_anim="idle")
                    else:
                        self.bed_state = "awake"
                        self.animator.play("idle", restart=True)
                save_pet(self.pet)
            else:
                sound.play("error")
            self.show_toast(msg)
            return None

        if action_id == "clean":
            ok, msg = self.pet.clean_room()
            if ok:
                sound.play("level_up" if msg.startswith("LEVEL UP!") else "clean")
                if self.bed_state == "awake":
                    self.animator.play("happy", restart=True, next_anim="idle")
                save_pet(self.pet)
            else:
                sound.play("error")
            self.show_toast(msg)
            return None

        if self.bed_state == "waking_up":
            sound.play("error")
            self.show_toast("Hold on, waking up!")
            return None

        if action_id == "train":
            ok, msg = self.pet.can_train()
            if ok:
                sound.play("select")
                save_pet(self.pet)
                return ("teach", {"pet": self.pet})
            sound.play("error")
            self.show_toast(msg)
            return None

        if action_id == "battle":
            ok, msg = self.pet.can_battle()
            if ok:
                sound.play("select")
                save_pet(self.pet)
                return ("battle", {"pet": self.pet})
            sound.play("error")
            self.show_toast(msg)
            return None

        if action_id == "play":
            ok, msg = self.pet.can_play()
            if ok:
                sound.play("select")
                save_pet(self.pet)
                return ("minigame", {"pet": self.pet})
            sound.play("error")
            self.show_toast(msg)
            return None

        if action_id == "feed":
            ok, msg = self.pet.feed()
            if ok:
                sound.play("level_up" if msg.startswith("LEVEL UP!") else "feed")
                self.animator.facing_left = False
                self.animator.play("eat", restart=True, next_anim="idle")
                save_pet(self.pet)
            else:
                sound.play("error")
            self.show_toast(msg)
            return None

        if action_id == "treat":
            ok, msg = self.pet.give_treat()
            if ok:
                sound.play("level_up" if msg.startswith("LEVEL UP!") else "treat")
                self.animator.facing_left = False
                self.animator.play("snack", restart=True, next_anim="idle")
                self.spawn_hearts(2)
                save_pet(self.pet)
            else:
                sound.play("error")
            self.show_toast(msg)
            return None

        if action_id == "hug":
            ok, msg = self.pet.hug()
            if ok:
                sound.play("level_up" if msg.startswith("LEVEL UP!") else "hug")
                self.animator.play("happy", restart=True, next_anim="idle")
                self.spawn_hearts(4)
                save_pet(self.pet)
            else:
                sound.play("error")
            self.show_toast(msg)
            return None

        return None

    def on_exit(self) -> None:
        save_pet(self.pet)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            sound.play("back")
            save_pet(self.pet)
            return ("title", {})

        if not self.pet.alive:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                sound.play("evolve")
                self.pet = Pet({"name": self.pet.name, "color": self.pet.color})
                self._load_pet_assets()
                self.walk_speed = 38.0 * self.pet.personality["walk_speed_mult"]
                self.bed_state = "awake"
                self.pet_x = 112.0
                self.target_x = self._pick_new_target(112.0)
                self.wander_timer = 0.8
                self.lamp_dim = 0.0
                save_pet(self.pet)
                self.animator.play("happy", restart=True, next_anim="idle")
                self.show_toast(f"A new {self.pet.name} hatched!")
            return None

        if event.key in KEYS_LEFT:
            self.action_idx = (self.action_idx - 1) % len(HOME_ACTIONS)
            self.label_timer = 1.8
            sound.play("click")
        elif event.key in KEYS_RIGHT:
            self.action_idx = (self.action_idx + 1) % len(HOME_ACTIONS)
            self.label_timer = 1.8
            sound.play("click")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.label_timer = 0.0
            return self._activate_selected_action()
        return None

    def update(self, dt: float) -> tuple[str, dict] | None:
        self.elapsed += dt
        time_scale = float(self.config.get("time_scale", 1.0))

        self.pet.update(dt, time_scale=time_scale)
        self.autosave_timer += dt
        if self.autosave_timer >= 30.0:
            save_pet(self.pet)
            self.autosave_timer = 0.0

        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_msg = ""

        if self.label_timer > 0:
            self.label_timer = max(0.0, self.label_timer - dt)

        for h in self.hearts:
            h["y"] -= h["vy"] * dt
            h["life"] -= dt
        self.hearts = [h for h in self.hearts if h["life"] > 0]

        # Bedtime & autonomous room roaming state machine
        if not self.pet.alive:
            self.bed_state = "awake"
            self.animator.play("idle")
        elif self.bed_state == "walking_to_bed":
            dx = WALK_TO_BED_X - self.pet_x
            if abs(dx) > 2.0:
                direction = 1.0 if dx > 0 else -1.0
                self.pet_x += direction * self.bed_walk_speed * dt
                self.animator.facing_left = direction < 0
                self.animator.play("walk")
            else:
                self.pet_x = float(WALK_TO_BED_X)
                self.animator.facing_left = False
                self.bed_state = "tucking_in"
                self.animator.play("sleep_start", restart=True, next_anim="sleep")
        elif self.bed_state == "tucking_in":
            if self.animator.current_name == "sleep":
                self.bed_state = "sleeping"
        elif self.bed_state == "sleeping":
            self.animator.facing_left = False
            self.animator.play("sleep")
        elif self.bed_state == "waking_up":
            if self.animator.current_name == "idle":
                self.bed_state = "awake"
                self.pet_x = float(WALK_TO_BED_X)
                self.target_x = 120.0
                self.wander_timer = 1.5
        elif not self.animator.is_playing_oneshot:
            dx = self.target_x - self.pet_x
            if abs(dx) > 2.0:
                direction = 1.0 if dx > 0 else -1.0
                self.pet_x += direction * self.walk_speed * dt
                self.animator.facing_left = direction < 0
                self.animator.play("walk")
            else:
                self.animator.play("idle")
                self.wander_timer -= dt
                if self.wander_timer <= 0:
                    if self.pet.happy >= 75.0 and random.random() < 0.25:
                        self.animator.play("happy", restart=True, next_anim="idle")
                        self.wander_timer = random.uniform(1.2, 2.2)
                    else:
                        self.target_x = self._pick_new_target(self.pet_x)
                        self.wander_timer = random.uniform(1.6, 3.8)

        if self.pet.alive:
            self.animator.update(dt)

        target_dim = 1.0 if self.bed_state in ("tucking_in", "sleeping") else 0.0
        if self.lamp_dim < target_dim:
            self.lamp_dim = min(target_dim, self.lamp_dim + dt * 1.6)
        elif self.lamp_dim > target_dim:
            self.lamp_dim = max(target_dim, self.lamp_dim - dt * 1.6)

        # Evolution check runs LAST so movement & animations always execute
        if self.pet.alive and self.bed_state == "awake" and not self.animator.is_playing_oneshot:
            evo_target = self.pet.check_evolution_ready()
            if evo_target:
                save_pet(self.pet)
                return ("evolve", {"pet": self.pet, "target_species": evo_target})

        return None

    def _draw_icon_dock(self, canvas: pygame.Surface) -> None:
        """Draws the bottom icon dock auto-sized to stay inside 320px."""
        dock_y = 146
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, dock_y, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, dock_y), (settings.LOGICAL_WIDTH, dock_y), 1)

        if not self.pet.alive:
            ctrl_surf = self.fonts["sans"].render("Enter: Hatch New Egg   Esc: Menu", True, settings.COLOR_MUTED)
            canvas.blit(ctrl_surf, ((settings.LOGICAL_WIDTH - ctrl_surf.get_width()) // 2, 151))
            return

        count = len(HOME_ACTIONS)
        margin = 4
        gap = 3 if count <= 9 else 2
        usable_w = settings.LOGICAL_WIDTH - margin * 2 - gap * (count - 1)
        slot_w = min(36, usable_w // count)
        slot_h = 20
        total_w = count * slot_w + (count - 1) * gap
        start_x = (settings.LOGICAL_WIDTH - total_w) // 2
        pulse_on = int(self.elapsed * 3.0) % 2 == 0

        sel_center_x = 0
        sel_label = ""

        for idx, (action_id, default_label) in enumerate(HOME_ACTIONS):
            sx = start_x + idx * (slot_w + gap)
            selected = idx == self.action_idx
            sy = dock_y + (1 if selected else 2)
            rect = pygame.Rect(sx, sy, slot_w, slot_h)

            if selected:
                pygame.draw.rect(canvas, DOCK_SLOT_SEL, rect, border_radius=4)
                pygame.draw.rect(canvas, BAR_GOOD, rect, 1, border_radius=4)
                cx = sx + slot_w // 2
                pygame.draw.polygon(canvas, BAR_GOOD, [(cx - 3, dock_y), (cx + 3, dock_y), (cx, dock_y - 3)])
                sel_center_x = cx
                sel_label = "Wake" if (action_id == "sleep" and self.pet.sleeping) else default_label
            else:
                pygame.draw.rect(canvas, DOCK_SLOT_BG, rect, border_radius=4)
                pygame.draw.rect(canvas, DOCK_SLOT_BORDER, rect, 1, border_radius=4)

            icon_key = "wake" if (action_id == "sleep" and self.pet.sleeping) else action_id
            icon_surf = self.icons[icon_key]
            canvas.blit(icon_surf, (sx + (slot_w - 14) // 2, sy + (slot_h - 14) // 2))

            if self._action_needs_alert(action_id) and pulse_on:
                pygame.draw.rect(canvas, BAR_LOW, (sx + slot_w - 6, sy + 2, 4, 4), border_radius=1)

        if self.label_timer > 0 and sel_label:
            lbl_surf = self.fonts["sans"].render(sel_label, True, settings.COLOR_TEXT)
            pill_w = lbl_surf.get_width() + 10
            pill_h = 16
            pill_x = max(4, min(settings.LOGICAL_WIDTH - pill_w - 4, sel_center_x - pill_w // 2))
            pill_y = dock_y - pill_h - 4
            pygame.draw.rect(canvas, settings.COLOR_PANEL, (pill_x, pill_y, pill_w, pill_h), border_radius=4)
            pygame.draw.rect(canvas, BAR_GOOD, (pill_x, pill_y, pill_w, pill_h), 1, border_radius=4)
            canvas.blit(lbl_surf, (pill_x + 5, pill_y + 1))

    def _draw_hud(self, canvas: pygame.Surface, clock_str: str) -> None:
        font_sans = self.fonts["sans"]
        font_mono = self.fonts["mono"]

        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 38))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 38), (settings.LOGICAL_WIDTH, 38), 1)

        header = font_sans.render(
            f"{self.pet.name} Lv{self.pet.level} B:{self.pet.bond}",
            True,
            settings.COLOR_TEXT,
        )
        canvas.blit(header, (6, 2))

        if not self.pet.alive:
            status_txt, status_col = "FAINT", BAR_LOW
        elif self.pet.sleeping:
            status_txt, status_col = "ZZZ", settings.COLOR_ACCENT
        elif len(self.pet.poops) > 0:
            status_txt, status_col = f"MESSx{len(self.pet.poops)}", BAR_WARN
        else:
            status_txt, status_col = "OK", BAR_GOOD

        right_surf = font_mono.render(f"{clock_str} {status_txt}", True, status_col)
        canvas.blit(right_surf, (settings.LOGICAL_WIDTH - right_surf.get_width() - 6, 2))

        slot_w = 78
        draw_stat_bar(canvas, font_mono, 4, 20, slot_w, "HG", self.pet.hunger)
        draw_stat_bar(canvas, font_mono, 83, 20, slot_w, "HP", self.pet.happy)
        draw_stat_bar(canvas, font_mono, 162, 20, slot_w, "EN", self.pet.energy)
        draw_stat_bar(canvas, font_mono, 241, 20, slot_w, "CL", self.pet.clean)

        if self.toast_msg:
            msg_surf = font_sans.render(self.toast_msg, True, settings.COLOR_TEXT)
            box_w = msg_surf.get_width() + 14
            box_x = (settings.LOGICAL_WIDTH - box_w) // 2
            pygame.draw.rect(canvas, settings.COLOR_PANEL, (box_x, 42, box_w, 18), border_radius=3)
            pygame.draw.rect(canvas, settings.COLOR_ACCENT, (box_x, 42, box_w, 18), 1, border_radius=3)
            canvas.blit(msg_surf, (box_x + 7, 44))

        self._draw_icon_dock(canvas)

    def render(self, canvas: pygame.Surface) -> None:
        hour_float, clock_str = self._get_clock_info()

        draw_room_decorations(canvas, self.pet, self.lamp_dim, self.elapsed)

        for px_pos in self.pet.poops:
            canvas.blit(self.poop_sprite, (px_pos, 114))

        in_bed_anim = self.bed_state in ("tucking_in", "sleeping", "waking_up")
        if in_bed_anim:
            pygame.draw.ellipse(canvas, (14, 10, 24), pygame.Rect(BED_X + 4, 123, 56, 8))
            canvas.blit(self.animator.get_frame(), (BED_X, int(self.pet_y)))
        else:
            pygame.draw.ellipse(canvas, (14, 10, 24), pygame.Rect(BED_X + 4, 123, 56, 8))
            canvas.blit(self.bed_sprite, (BED_X, int(self.pet_y)))
            pygame.draw.ellipse(canvas, (18, 12, 28), pygame.Rect(int(self.pet_x) + 14, 124, 36, 7))
            canvas.blit(self.animator.get_frame(), (int(self.pet_x), int(self.pet_y)))

        if self.lamp_dim > 0.01:
            self.dim_overlay.fill((8, 4, 20, int(self.lamp_dim * 120)))
            canvas.blit(self.dim_overlay, (0, 38))

        draw_clock_window(canvas, hour_float, self.elapsed)

        if self.pet.alive and self.bed_state == "sleeping":
            bob = int(math.sin(self.elapsed * 2.5) * 3)
            zzz = self.fonts["mono"].render("Zzz", True, settings.COLOR_ACCENT)
            canvas.blit(zzz, (BED_X + 42, int(self.pet_y) + 10 + bob))

        need = self.pet.get_need_bubble()
        if need and self.bed_state == "awake" and not self.animator.is_playing_oneshot:
            bubble_bob = int(math.sin(self.elapsed * 4.0) * 2)
            draw_thought_bubble(canvas, int(self.pet_x) + 44, int(self.pet_y) - 6 + bubble_bob, need)

        for h in self.hearts:
            draw_pixel_heart(canvas, int(h["x"]), int(h["y"]))

        self._draw_hud(canvas, clock_str)