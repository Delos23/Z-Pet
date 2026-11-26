"""Generates 32x32 pixel-art sprite sheets for all 35 Z-Pet species:
5 Babies + 15 Care-Driven Teens + 15 Care-Driven Adults.

Uses exact BASE_SOURCE_COLORS from core/animator.py so all 7 base colors swap cleanly.
Existing spark_kit sprites are preserved unless --force-all is passed.
"""

from pathlib import Path
import sys
import pygame

ROOT = Path(__file__).resolve().parent.parent
SPRITES_ROOT = ROOT / "assets" / "sprites"

# Exact recolorable coat colors (matched by core/animator.py)
BODY  = (145, 98, 225, 255)
LIGHT = (196, 162, 255, 255)
BELLY = (240, 232, 255, 255)
EYE   = (255, 236, 110, 255)

# Fixed detail & prop colors (untouched by base color swap)
OUT      = (28, 18, 42, 255)
CHEEK    = (255, 132, 178, 255)
GOLD     = (255, 212, 88, 255)
GOLD_HI  = (255, 244, 176, 255)
CRYSTAL  = (128, 232, 255, 255)
METAL    = (164, 174, 198, 255)
METAL_HI = (218, 226, 242, 255)
LEAF     = (86, 198, 112, 255)
LEAF_HI  = (146, 236, 152, 255)
FLOWER   = (255, 134, 188, 255)
THORN    = (156, 78, 92, 255)
EMBER    = (245, 118, 66, 255)
NEON     = (98, 244, 214, 255)
WOOD     = (142, 92, 62, 255)
FOOD_BOWL = (198, 86, 114, 255)
FOOD_FILL = (232, 168, 92, 255)
BALL_COL  = (242, 92, 132, 255)
BALL_HI   = (255, 198, 214, 255)
BED_RIM   = (92, 58, 136, 255)
BED_PAD   = (156, 112, 214, 255)
BED_TRIM  = (224, 196, 255, 255)
BLANKET_MAIN  = (122, 82, 184, 255)
BLANKET_SHADE = (94, 60, 148, 255)
BLANKET_CUFF  = (232, 212, 255, 255)
BLANKET_STAR  = (255, 224, 128, 255)

def rect_out(surf: pygame.Surface, x: int, y: int, w: int, h: int, fill: tuple) -> None:
    pygame.draw.rect(surf, OUT, (x - 1, y - 1, w + 2, h + 2))
    pygame.draw.rect(surf, fill, (x, y, w, h))


def draw_bed(surf: pygame.Surface) -> None:
    """Draws a front-facing bed (headboard + centered pillow at top, frame at bottom)."""
    # Corner headboard posts
    pygame.draw.rect(surf, OUT, (4, 11, 3, 4))
    pygame.draw.rect(surf, OUT, (25, 11, 3, 4))
    pygame.draw.rect(surf, BED_TRIM, (5, 12, 1, 2))
    pygame.draw.rect(surf, BED_TRIM, (26, 12, 1, 2))

    # Headboard panel
    pygame.draw.rect(surf, OUT, (4, 13, 24, 9))
    pygame.draw.rect(surf, BED_RIM, (5, 14, 22, 7))
    pygame.draw.rect(surf, BED_PAD, (5, 14, 22, 1))

    # Centered pillow
    pygame.draw.rect(surf, OUT, (8, 16, 16, 6))
    pygame.draw.rect(surf, BED_TRIM, (9, 17, 14, 4))
    pygame.draw.rect(surf, BED_PAD, (9, 20, 14, 1))

    # Mattress & lower frame
    pygame.draw.rect(surf, OUT, (3, 20, 26, 9))
    pygame.draw.rect(surf, BED_RIM, (4, 21, 24, 7))
    pygame.draw.rect(surf, BED_PAD, (5, 21, 22, 5))

    # Bed feet
    pygame.draw.rect(surf, OUT, (4, 28, 4, 2))
    pygame.draw.rect(surf, OUT, (24, 28, 4, 2))
    pygame.draw.rect(surf, BED_RIM, (5, 28, 2, 1))
    pygame.draw.rect(surf, BED_RIM, (25, 28, 2, 1))


def draw_bed(surf: pygame.Surface) -> None:
    """Draws a front-facing bed (headboard + centered pillow at top, frame at bottom)."""
    # Corner headboard posts
    pygame.draw.rect(surf, OUT, (4, 11, 3, 4))
    pygame.draw.rect(surf, OUT, (25, 11, 3, 4))
    pygame.draw.rect(surf, BED_TRIM, (5, 12, 1, 2))
    pygame.draw.rect(surf, BED_TRIM, (26, 12, 1, 2))

    # Headboard panel
    pygame.draw.rect(surf, OUT, (4, 13, 24, 9))
    pygame.draw.rect(surf, BED_RIM, (5, 14, 22, 7))
    pygame.draw.rect(surf, BED_PAD, (5, 14, 22, 1))

    # Centered pillow
    pygame.draw.rect(surf, OUT, (8, 16, 16, 6))
    pygame.draw.rect(surf, BED_TRIM, (9, 17, 14, 4))
    pygame.draw.rect(surf, BED_PAD, (9, 20, 14, 1))

    # Mattress & lower frame
    pygame.draw.rect(surf, OUT, (3, 20, 26, 9))
    pygame.draw.rect(surf, BED_RIM, (4, 21, 24, 7))
    pygame.draw.rect(surf, BED_PAD, (5, 21, 22, 5))

    # Bed feet
    pygame.draw.rect(surf, OUT, (4, 28, 4, 2))
    pygame.draw.rect(surf, OUT, (24, 28, 4, 2))
    pygame.draw.rect(surf, BED_RIM, (5, 28, 2, 1))
    pygame.draw.rect(surf, BED_RIM, (25, 28, 2, 1))


def draw_blanket(surf: pygame.Surface, coverage: int = 2, breathe: int = 0) -> None:
    """Draws a front-facing quilt (0=folded at foot, 1=half-pulled, 2=tucked to chin)."""
    if coverage == 0:
        # Folded horizontally across the bottom foot of the bed
        pygame.draw.rect(surf, OUT, (4, 23, 24, 6))
        pygame.draw.rect(surf, BLANKET_MAIN, (5, 24, 22, 4))
        pygame.draw.rect(surf, BLANKET_SHADE, (5, 26, 22, 2))
        pygame.draw.rect(surf, BLANKET_CUFF, (5, 24, 22, 1))
        surf.set_at((15, 26), BLANKET_STAR)
    elif coverage == 1:
        # Pulled halfway up horizontally
        pygame.draw.rect(surf, OUT, (4, 20, 24, 9))
        pygame.draw.rect(surf, BLANKET_MAIN, (5, 21, 22, 7))
        pygame.draw.rect(surf, BLANKET_SHADE, (5, 26, 22, 2))
        pygame.draw.rect(surf, BLANKET_CUFF, (5, 21, 22, 2))
        pygame.draw.line(surf, OUT, (5, 23), (26, 23))
        surf.set_at((11, 24), BLANKET_STAR)
        surf.set_at((20, 25), BLANKET_STAR)
    else:
        # Tucked up to the chin with a 1px breathing shift
        top_y = 18 + breathe
        pygame.draw.rect(surf, OUT, (4, top_y - 1, 24, 30 - top_y))
        pygame.draw.rect(surf, BLANKET_MAIN, (5, top_y, 22, 28 - top_y))
        pygame.draw.rect(surf, BLANKET_SHADE, (5, 26, 22, 2))
        pygame.draw.rect(surf, BLANKET_CUFF, (5, top_y, 22, 2))
        pygame.draw.line(surf, OUT, (5, top_y + 2), (26, top_y + 2))
        surf.set_at((10, top_y + 4), BLANKET_STAR)
        surf.set_at((17, top_y + 5), BLANKET_STAR)
        surf.set_at((22, top_y + 4), BLANKET_STAR)

def draw_eyes(surf: pygame.Surface, lx: int, rx: int, y: int, mode: str = "open") -> None:
    if mode == "closed":
        pygame.draw.line(surf, OUT, (lx, y + 1), (lx + 2, y + 1))
        pygame.draw.line(surf, OUT, (rx, y + 1), (rx + 2, y + 1))
    elif mode == "happy":
        pygame.draw.rect(surf, OUT, (lx, y, 2, 1))
        pygame.draw.rect(surf, OUT, (lx + 1, y - 1, 1, 1))
        pygame.draw.rect(surf, OUT, (rx, y, 2, 1))
        pygame.draw.rect(surf, OUT, (rx + 1, y - 1, 1, 1))
    else:
        pygame.draw.rect(surf, OUT, (lx, y, 2, 3))
        pygame.draw.rect(surf, EYE, (lx, y, 2, 2))
        pygame.draw.rect(surf, OUT, (rx, y, 2, 3))
        pygame.draw.rect(surf, EYE, (rx, y, 2, 2))


def draw_creature(
    surf: pygame.Surface,
    species_id: str,
    dx: int = 0,
    dy: int = 0,
    step: int = 0,
    eye_mode: str = "open",
    mouth_open: bool = False,
) -> None:
    cx = 16 + dx
    by = 20 + dy
    leg_l = 1 if step == 1 else (-1 if step == 3 else 0)
    leg_r = -leg_l
    wing_bob = -1 if step in (1, 3) else 0
    hover = -1 if step in (1, 3) else 0

    # ===================== 5 BABIES (compact, chubby) =====================
    if species_id == "spark_kit":
        pygame.draw.rect(surf, OUT, (cx - 10, by - 8, 4, 4))
        pygame.draw.rect(surf, LIGHT, (cx - 9, by - 7, 2, 2))
        rect_out(surf, cx - 5, by + 5 + leg_l, 3, 3, BODY)
        rect_out(surf, cx + 2, by + 5 + leg_r, 3, 3, BODY)
        rect_out(surf, cx - 6, by - 4, 12, 10, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by, 6, 5))
        rect_out(surf, cx - 6, by - 12, 3, 4, BODY)
        rect_out(surf, cx + 3, by - 12, 3, 4, BODY)
        pygame.draw.rect(surf, LIGHT, (cx - 5, by - 11, 1, 2))
        pygame.draw.rect(surf, LIGHT, (cx + 4, by - 11, 1, 2))
        rect_out(surf, cx - 6, by - 9, 12, 8, BODY)
        pygame.draw.rect(surf, LIGHT, (cx - 4, by - 9, 8, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 6, eye_mode)
        surf.set_at((cx - 5, by - 3), CHEEK)
        surf.set_at((cx + 4, by - 3), CHEEK)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx - 1, by - 3, 2, 2))

    elif species_id == "cinder_pup":
        rect_out(surf, cx - 10, by - 5, 4, 4, BODY)
        pygame.draw.rect(surf, EMBER, (cx - 10, by - 7, 3, 3))
        rect_out(surf, cx - 6, by + 5 + leg_l, 3, 3, BODY)
        rect_out(surf, cx + 3, by + 5 + leg_r, 3, 3, BODY)
        rect_out(surf, cx - 7, by - 3, 14, 9, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by, 7, 5))
        rect_out(surf, cx - 6, by - 10, 12, 8, BODY)
        rect_out(surf, cx + 4, by - 6, 4, 4, LIGHT)
        pygame.draw.rect(surf, OUT, (cx + 7, by - 6, 2, 1))
        rect_out(surf, cx - 7, by - 11, 3, 5, LIGHT)
        rect_out(surf, cx + 1, by - 13, 3, 4, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 2, by - 13, 3, 3))
        draw_eyes(surf, cx - 3, cx + 2, by - 7, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 4, by - 3, 2, 2))

    elif species_id == "aqua_fin":
        rect_out(surf, cx - 11, by - 2, 5, 5, LIGHT)
        pygame.draw.rect(surf, CRYSTAL, (cx - 11, by - 3, 2, 7))
        rect_out(surf, cx - 5, by + 5 + leg_l, 3, 2, LIGHT)
        rect_out(surf, cx + 2, by + 5 + leg_r, 3, 2, LIGHT)
        rect_out(surf, cx - 6, by - 5, 13, 11, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 1, 7, 6))
        rect_out(surf, cx - 6, by - 10, 12, 8, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx - 2, by - 13, 4, 3))
        pygame.draw.rect(surf, OUT, (cx - 9, by - 8, 3, 4))
        pygame.draw.rect(surf, CRYSTAL, (cx - 8, by - 7, 2, 2))
        pygame.draw.rect(surf, OUT, (cx + 6, by - 8, 3, 4))
        pygame.draw.rect(surf, CRYSTAL, (cx + 6, by - 7, 2, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 7, eye_mode)
        surf.set_at((cx - 5, by - 4), CHEEK)
        surf.set_at((cx + 4, by - 4), CHEEK)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx - 1, by - 4, 2, 2))

    elif species_id == "sprout_owl":
        rect_out(surf, cx - 4, by + 5 + leg_l, 3, 2, GOLD)
        rect_out(surf, cx + 1, by + 5 + leg_r, 3, 2, GOLD)
        rect_out(surf, cx - 8, by - 4 + wing_bob, 3, 7, LIGHT)
        rect_out(surf, cx + 5, by - 4 + wing_bob, 3, 7, LIGHT)
        rect_out(surf, cx - 6, by - 9, 12, 15, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 4, by - 1, 8, 6))
        pygame.draw.rect(surf, OUT, (cx - 1, by - 13, 2, 4))
        pygame.draw.rect(surf, LEAF, (cx - 5, by - 15, 4, 3))
        pygame.draw.rect(surf, LEAF_HI, (cx + 1, by - 15, 4, 3))
        draw_eyes(surf, cx - 4, cx + 2, by - 6, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 3, 2, 2 if not mouth_open else 3))

    elif species_id == "cog_bit":
        rect_out(surf, cx - 12, by - 7 + hover, 5, 6, METAL)
        rect_out(surf, cx + 7, by - 7 + hover, 5, 6, METAL)
        pygame.draw.rect(surf, NEON, (cx - 11, by - 5 + hover, 3, 2))
        pygame.draw.rect(surf, NEON, (cx + 8, by - 5 + hover, 3, 2))
        pygame.draw.rect(surf, OUT, (cx - 1, by - 14 + hover, 2, 4))
        pygame.draw.rect(surf, GOLD, (cx - 2, by - 16 + hover, 4, 3))
        rect_out(surf, cx - 7, by - 9 + hover, 14, 12, BODY)
        pygame.draw.rect(surf, METAL, (cx - 7, by - 1 + hover, 14, 3))
        pygame.draw.rect(surf, LIGHT, (cx - 5, by - 9 + hover, 10, 2))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 7 + hover, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 6 + hover, eye_mode)
        rect_out(surf, cx - 4, by + 3 + hover, 3, 2, METAL)
        rect_out(surf, cx + 1, by + 3 + hover, 3, 2, METAL)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 1, by - 2 + hover, 2, 2))

    # ===================== 15 TEENS (medium, care-styled) =====================
    elif species_id == "star_lynx":
        # Radiant Cat Teen: sleek posture, glowing forehead star, wispy tail & scarf fluff
        rect_out(surf, cx - 11, by - 9, 5, 3, LIGHT)
        pygame.draw.rect(surf, GOLD_HI, (cx - 11, by - 10, 2, 2))
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 6, by - 5, 12, 10, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 3, 6, 6))
        pygame.draw.rect(surf, CRYSTAL, (cx - 1, by - 2, 2, 2))
        rect_out(surf, cx - 6, by - 15, 3, 5, BODY)
        rect_out(surf, cx + 3, by - 15, 3, 5, BODY)
        rect_out(surf, cx - 6, by - 11, 12, 8, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 11, 2, 2))  # Forehead star
        draw_eyes(surf, cx - 4, cx + 2, by - 8, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx - 1, by - 5, 2, 2))

    elif species_id == "jolt_kat":
        # Trained Cat Teen: bolt-tip ears, gold headband/collar, athletic stance
        rect_out(surf, cx - 11, by - 8, 5, 3, GOLD)
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 6, by - 5, 13, 10, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 5, by - 5, 11, 2))  # Combat collar
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 2, 6, 5))
        rect_out(surf, cx - 6, by - 15, 3, 5, BODY)
        rect_out(surf, cx + 3, by - 15, 3, 5, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 6, by - 16, 2, 2))
        pygame.draw.rect(surf, GOLD, (cx + 4, by - 16, 2, 2))
        rect_out(surf, cx - 6, by - 11, 12, 8, BODY)
        draw_eyes(surf, cx - 3, cx + 2, by - 8, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx - 1, by - 5, 2, 2))

    elif species_id == "feral_volt":
        # Wild Cat Teen: scruffy swept ears, neon tail spark, spiky back fur
        rect_out(surf, cx - 12, by - 9, 5, 4, NEON)
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 7, by - 5, 14, 10, BODY)
        pygame.draw.rect(surf, NEON, (cx - 5, by - 7, 3, 2))
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 2, 6, 5))
        rect_out(surf, cx - 8, by - 14, 4, 4, LIGHT)
        rect_out(surf, cx + 4, by - 14, 4, 4, LIGHT)
        rect_out(surf, cx - 6, by - 11, 12, 8, BODY)
        draw_eyes(surf, cx - 3, cx + 2, by - 8, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, GOLD_HI, (cx - 1, by - 5, 3, 2))

    elif species_id == "sun_pup":
        # Radiant Pup Teen: golden chest ruff, bright sun dot on brow
        rect_out(surf, cx - 11, by - 7, 4, 4, GOLD)
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 7, by - 5, 14, 10, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 4, by - 5, 10, 4))
        pygame.draw.rect(surf, GOLD_HI, (cx - 2, by - 4, 6, 2))
        rect_out(surf, cx - 6, by - 12, 12, 8, BODY)
        rect_out(surf, cx + 4, by - 8, 4, 4, LIGHT)
        pygame.draw.rect(surf, GOLD_HI, (cx - 1, by - 14, 3, 2))
        draw_eyes(surf, cx - 3, cx + 2, by - 9, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 4, by - 5, 2, 2))

    elif species_id == "blaze_hound":
        # Trained Pup Teen: budding gold horns, fiery mane tuft
        rect_out(surf, cx - 11, by - 7, 4, 5, EMBER)
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 7, by - 5, 15, 10, BODY)
        pygame.draw.rect(surf, EMBER, (cx - 5, by - 6, 7, 3))
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 1, 6, 5))
        rect_out(surf, cx - 6, by - 12, 12, 8, BODY)
        rect_out(surf, cx + 4, by - 8, 4, 4, LIGHT)
        rect_out(surf, cx - 6, by - 15, 2, 3, GOLD)
        rect_out(surf, cx + 1, by - 15, 2, 3, GOLD)
        draw_eyes(surf, cx - 3, cx + 2, by - 9, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 4, by - 5, 2, 2))

    elif species_id == "char_fang":
        # Wild Pup Teen: charcoal back spikes, rough metal jaw trim
        rect_out(surf, cx - 12, by - 6, 5, 4, METAL)
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 7, by - 5, 15, 10, BODY)
        pygame.draw.rect(surf, EMBER, (cx - 6, by - 8, 3, 3))
        pygame.draw.rect(surf, EMBER, (cx - 1, by - 8, 3, 3))
        rect_out(surf, cx - 5, by - 12, 12, 8, BODY)
        rect_out(surf, cx + 4, by - 8, 5, 3, METAL_HI)
        draw_eyes(surf, cx - 2, cx + 3, by - 9, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, EMBER, (cx + 4, by - 6, 3, 2))

    elif species_id == "reef_kin":
        # Radiant Sea Teen: budding crystal shell on back, pearl crown
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 9, by - 8, 12, 10, LIGHT)
        pygame.draw.rect(surf, CRYSTAL, (cx - 7, by - 10, 8, 3))
        rect_out(surf, cx - 6, by - 2, 13, 7, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by, 7, 4))
        rect_out(surf, cx + 1, by - 11, 9, 8, BODY)
        pygame.draw.rect(surf, GOLD_HI, (cx + 4, by - 13, 3, 2))
        draw_eyes(surf, cx + 3, cx + 7, by - 8, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 6, by - 4, 2, 2))

    elif species_id == "wave_crest":
        # Trained Sea Teen: streamlined aqua drake-ling with sharp dorsal fin
        rect_out(surf, cx - 12, by - 3, 6, 4, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx - 13, by - 6, 3, 6))
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 6, by - 6, 12, 11, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx - 7, by - 10, 4, 4))
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 3, 6, 7))
        rect_out(surf, cx - 4, by - 13, 11, 8, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx - 5, by - 15, 4, 2))
        draw_eyes(surf, cx - 1, cx + 4, by - 10, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 3, by - 6, 2, 2))

    elif species_id == "murk_fin":
        # Wild Sea Teen: budding glowing neon angler stalk & dark spiky fin
        rect_out(surf, cx - 12, by - 4, 5, 5, BODY)
        pygame.draw.rect(surf, NEON, (cx - 12, by - 3, 2, 3))
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 6, by - 7, 14, 12, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 2, 7, 6))
        pygame.draw.rect(surf, OUT, (cx + 1, by - 13, 2, 6))
        pygame.draw.rect(surf, NEON, (cx + 3, by - 13, 3, 2))
        draw_eyes(surf, cx - 2, cx + 4, by - 5, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, GOLD_HI, (cx + 2, by - 1, 4, 2))

    elif species_id == "petal_owl":
        # Radiant Owl Teen: leafy wings & blooming pink flower bud on head
        rect_out(surf, cx - 4, by + 4 + leg_l, 3, 3, GOLD)
        rect_out(surf, cx + 1, by + 4 + leg_r, 3, 3, GOLD)
        rect_out(surf, cx - 11, by - 7 + wing_bob, 5, 9, LEAF)
        rect_out(surf, cx + 6, by - 7 + wing_bob, 5, 9, LEAF)
        rect_out(surf, cx - 6, by - 11, 12, 16, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 4, by - 3, 8, 7))
        pygame.draw.rect(surf, LEAF_HI, (cx - 4, by - 13, 8, 2))
        pygame.draw.rect(surf, FLOWER, (cx - 2, by - 16, 4, 3))
        draw_eyes(surf, cx - 4, cx + 2, by - 8, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 5, 2, 2 if not mouth_open else 3))

    elif species_id == "bark_wing":
        # Trained Owl Teen: sturdy wooden shoulder armor & armored brow
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, WOOD)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, WOOD)
        rect_out(surf, cx - 10, by - 8 + wing_bob, 4, 9, WOOD)
        rect_out(surf, cx + 6, by - 8 + wing_bob, 4, 9, WOOD)
        rect_out(surf, cx - 6, by - 11, 12, 16, BODY)
        pygame.draw.rect(surf, WOOD, (cx - 4, by - 3, 8, 5))
        pygame.draw.rect(surf, LEAF, (cx - 4, by - 13, 8, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 8, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 5, 2, 2 if not mouth_open else 3))

    elif species_id == "bramblet":
        # Wild Owl Teen: budding thorn tufts & jagged thorn-tipped wings
        rect_out(surf, cx - 4, by + 4 + leg_l, 3, 3, THORN)
        rect_out(surf, cx + 1, by + 4 + leg_r, 3, 3, THORN)
        rect_out(surf, cx - 10, by - 7 + wing_bob, 4, 9, THORN)
        rect_out(surf, cx + 6, by - 7 + wing_bob, 4, 9, THORN)
        rect_out(surf, cx - 6, by - 11, 12, 16, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 2, 6, 6))
        rect_out(surf, cx - 7, by - 15, 2, 4, THORN)
        rect_out(surf, cx + 5, by - 15, 2, 4, THORN)
        draw_eyes(surf, cx - 4, cx + 2, by - 8, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 5, 2, 3))

    elif species_id == "gild_bot":
        # Radiant Bot Teen: brass clockwork wings & thin halo antenna
        rect_out(surf, cx - 12, by - 9 + hover, 5, 7, GOLD)
        rect_out(surf, cx + 7, by - 9 + hover, 5, 7, GOLD)
        pygame.draw.rect(surf, GOLD_HI, (cx - 11, by - 8 + hover, 3, 2))
        pygame.draw.rect(surf, GOLD_HI, (cx + 8, by - 8 + hover, 3, 2))
        pygame.draw.rect(surf, GOLD, (cx - 4, by - 16 + hover, 8, 2))
        rect_out(surf, cx - 7, by - 11 + hover, 14, 14, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 3, by - 2 + hover, 6, 4))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 9 + hover, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 8 + hover, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, CRYSTAL, (cx - 1, by - 4 + hover, 2, 2))

    elif species_id == "gear_unit":
        # Trained Bot Teen: compact bipedal armored unit with steel shoulders
        rect_out(surf, cx - 6, by + 3 + leg_l, 4, 5, METAL)
        rect_out(surf, cx + 2, by + 3 + leg_r, 4, 5, METAL)
        rect_out(surf, cx - 10, by - 10, 4, 5, METAL)
        rect_out(surf, cx + 6, by - 10, 4, 5, METAL)
        rect_out(surf, cx - 7, by - 11, 14, 14, BODY)
        pygame.draw.rect(surf, METAL_HI, (cx - 5, by - 3, 10, 5))
        pygame.draw.rect(surf, NEON, (cx - 1, by - 2, 2, 3))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 9, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 8, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 1, by - 4, 2, 2))

    elif species_id == "static_bit":
        # Wild Bot Teen: crooked neon glitch wings & twin static sparks
        rect_out(surf, cx - 13, by - 9 + hover, 5, 4, NEON)
        rect_out(surf, cx + 8, by - 6 + hover, 5, 4, NEON)
        pygame.draw.rect(surf, NEON, (cx - 5, by - 15 + hover, 2, 4))
        pygame.draw.rect(surf, NEON, (cx + 3, by - 14 + hover, 2, 3))
        rect_out(surf, cx - 7, by - 11 + hover, 14, 13, BODY)
        pygame.draw.rect(surf, LIGHT, (cx - 4, by + 2 + hover, 8, 2))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 9 + hover, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 8 + hover, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 2, by - 4 + hover, 4, 2))

    # ===================== 15 ADULTS (full-size, majestic/fierce) =====================
    elif species_id == "aether_cat":
        rect_out(surf, cx - 12, by - 9, 5, 3, LIGHT)
        rect_out(surf, cx - 11, by - 4, 5, 3, BODY)
        rect_out(surf, cx - 5, by + 3 + leg_l, 3, 5, BODY)
        rect_out(surf, cx + 2, by + 3 + leg_r, 3, 5, BODY)
        rect_out(surf, cx - 6, by - 6, 12, 10, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 4, 6, 7))
        pygame.draw.rect(surf, CRYSTAL, (cx - 1, by - 2, 2, 3))
        rect_out(surf, cx - 6, by - 16, 3, 5, BODY)
        rect_out(surf, cx + 3, by - 16, 3, 5, BODY)
        pygame.draw.rect(surf, OUT, (cx - 5, by - 19, 10, 3))
        pygame.draw.rect(surf, GOLD, (cx - 4, by - 18, 8, 1))
        pygame.draw.rect(surf, GOLD_HI, (cx - 2, by - 18, 4, 1))
        rect_out(surf, cx - 6, by - 13, 12, 8, BODY)
        pygame.draw.rect(surf, LIGHT, (cx - 4, by - 13, 8, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 10, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx - 1, by - 6, 2, 2))

    elif species_id == "volt_lynx":
        rect_out(surf, cx - 12, by - 10, 4, 3, GOLD)
        rect_out(surf, cx - 10, by - 7, 4, 4, LIGHT)
        rect_out(surf, cx - 6, by + 3 + leg_l, 3, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 3, 5, BODY)
        rect_out(surf, cx - 7, by - 6, 14, 10, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 5, 7, 7))
        pygame.draw.rect(surf, GOLD, (cx, by - 4, 3, 4))
        rect_out(surf, cx - 6, by - 17, 3, 6, BODY)
        rect_out(surf, cx + 3, by - 17, 3, 6, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 6, by - 18, 2, 2))
        pygame.draw.rect(surf, GOLD, (cx + 4, by - 18, 2, 2))
        rect_out(surf, cx - 6, by - 13, 13, 8, BODY)
        pygame.draw.rect(surf, LIGHT, (cx - 4, by - 13, 9, 2))
        draw_eyes(surf, cx - 3, cx + 3, by - 10, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx, by - 6, 3, 2))

    elif species_id == "storm_claw":
        rect_out(surf, cx - 13, by - 11, 5, 4, NEON)
        rect_out(surf, cx - 10, by - 7, 4, 4, BODY)
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, BODY)
        pygame.draw.rect(surf, GOLD_HI, (cx + 6, by + 6 + leg_r, 2, 2))
        rect_out(surf, cx - 8, by - 7, 16, 11, BODY)
        pygame.draw.rect(surf, NEON, (cx - 6, by - 9, 4, 3))
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 3, 7, 6))
        rect_out(surf, cx - 6, by - 15, 13, 9, BODY)
        rect_out(surf, cx - 8, by - 17, 4, 4, LIGHT)
        rect_out(surf, cx + 4, by - 17, 4, 4, LIGHT)
        draw_eyes(surf, cx - 3, cx + 3, by - 11, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, GOLD_HI, (cx, by - 7, 3, 2))

    elif species_id == "sol_hound":
        rect_out(surf, cx - 12, by - 9, 5, 5, GOLD_HI)
        rect_out(surf, cx - 6, by + 3 + leg_l, 3, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 3, 5, BODY)
        rect_out(surf, cx - 7, by - 6, 15, 10, BODY)
        rect_out(surf, cx - 4, by - 8, 12, 7, GOLD)
        pygame.draw.rect(surf, GOLD_HI, (cx - 2, by - 7, 8, 3))
        rect_out(surf, cx - 5, by - 15, 12, 9, BODY)
        rect_out(surf, cx + 5, by - 10, 4, 4, LIGHT)
        pygame.draw.rect(surf, GOLD_HI, (cx - 1, by - 18, 4, 3))
        draw_eyes(surf, cx - 2, cx + 3, by - 12, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 5, by - 7, 3, 2))

    elif species_id == "pyro_fang":
        rect_out(surf, cx - 12, by - 9, 5, 6, EMBER)
        pygame.draw.rect(surf, GOLD_HI, (cx - 11, by - 8, 2, 3))
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, BODY)
        rect_out(surf, cx - 8, by - 6, 16, 10, BODY)
        pygame.draw.rect(surf, LIGHT, (cx - 4, by - 6, 10, 5))
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 1, 7, 5))
        rect_out(surf, cx - 6, by - 14, 13, 9, BODY)
        rect_out(surf, cx + 5, by - 9, 4, 4, LIGHT)
        rect_out(surf, cx - 7, by - 18, 3, 5, GOLD)
        rect_out(surf, cx + 2, by - 18, 3, 5, GOLD)
        draw_eyes(surf, cx - 3, cx + 3, by - 11, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 5, by - 6, 3, 2))

    elif species_id == "ash_maw":
        rect_out(surf, cx - 13, by - 6, 6, 4, METAL)
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, BODY)
        rect_out(surf, cx - 8, by - 7, 17, 11, BODY)
        pygame.draw.rect(surf, EMBER, (cx - 7, by - 10, 4, 3))
        pygame.draw.rect(surf, EMBER, (cx - 1, by - 10, 4, 3))
        rect_out(surf, cx - 5, by - 15, 13, 9, BODY)
        rect_out(surf, cx + 4, by - 9, 6, 4, METAL_HI)
        draw_eyes(surf, cx - 2, cx + 4, by - 12, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, EMBER, (cx + 5, by - 7, 3, 2))

    elif species_id == "coral_shell":
        rect_out(surf, cx - 7, by + 4 + leg_l, 4, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 4, 4, BODY)
        rect_out(surf, cx - 10, by - 10, 15, 12, LIGHT)
        pygame.draw.rect(surf, CRYSTAL, (cx - 8, by - 12, 11, 4))
        pygame.draw.rect(surf, CRYSTAL, (cx - 9, by - 7, 4, 4))
        pygame.draw.rect(surf, GOLD, (cx - 3, by - 13, 3, 3))
        rect_out(surf, cx - 7, by - 1, 14, 6, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 4, by + 1, 9, 3))
        rect_out(surf, cx + 2, by - 11, 9, 9, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx + 3, by - 13, 4, 2))
        draw_eyes(surf, cx + 4, cx + 8, by - 8, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 7, by - 4, 3, 2))

    elif species_id == "tide_drake":
        rect_out(surf, cx - 13, by - 4, 7, 4, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx - 14, by - 7, 3, 7))
        rect_out(surf, cx - 8, by - 13, 6, 6, CRYSTAL)
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 6, by - 6, 13, 11, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 1, by - 4, 6, 8))
        rect_out(surf, cx - 4, by - 15, 12, 9, BODY)
        pygame.draw.rect(surf, CRYSTAL, (cx - 6, by - 17, 5, 3))
        pygame.draw.rect(surf, GOLD, (cx + 1, by - 14, 2, 2))
        draw_eyes(surf, cx - 1, cx + 4, by - 11, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, OUT, (cx + 4, by - 7, 3, 2))

    elif species_id == "abyss_fin":
        rect_out(surf, cx - 13, by - 5, 6, 6, BODY)
        pygame.draw.rect(surf, NEON, (cx - 13, by - 4, 2, 4))
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 7, by - 8, 15, 13, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 2, 8, 6))
        pygame.draw.rect(surf, OUT, (cx + 1, by - 16, 2, 8))
        pygame.draw.rect(surf, OUT, (cx + 3, by - 16, 4, 2))
        pygame.draw.rect(surf, NEON, (cx + 6, by - 14, 3, 3))
        draw_eyes(surf, cx - 2, cx + 4, by - 6, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, GOLD_HI, (cx + 2, by - 1, 5, 2))

    elif species_id == "bloom_wing":
        rect_out(surf, cx - 4, by + 4 + leg_l, 3, 4, GOLD)
        rect_out(surf, cx + 1, by + 4 + leg_r, 3, 4, GOLD)
        rect_out(surf, cx - 13, by - 9 + wing_bob, 6, 11, LEAF)
        rect_out(surf, cx + 7, by - 9 + wing_bob, 6, 11, LEAF)
        pygame.draw.rect(surf, FLOWER, (cx - 12, by - 8 + wing_bob, 3, 3))
        pygame.draw.rect(surf, FLOWER, (cx + 9, by - 8 + wing_bob, 3, 3))
        rect_out(surf, cx - 7, by - 13, 14, 18, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 4, by - 4, 8, 8))
        pygame.draw.rect(surf, LEAF_HI, (cx - 5, by - 16, 10, 3))
        pygame.draw.rect(surf, FLOWER, (cx - 2, by - 18, 4, 4))
        pygame.draw.rect(surf, GOLD_HI, (cx - 1, by - 17, 2, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 9, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 6, 2, 2 if not mouth_open else 3))

    elif species_id == "iron_bark":
        rect_out(surf, cx - 6, by + 3 + leg_l, 4, 5, METAL)
        rect_out(surf, cx + 2, by + 3 + leg_r, 4, 5, METAL)
        rect_out(surf, cx - 11, by - 10 + wing_bob, 5, 11, METAL)
        rect_out(surf, cx + 6, by - 10 + wing_bob, 5, 11, METAL)
        rect_out(surf, cx - 7, by - 14, 14, 18, BODY)
        rect_out(surf, cx - 4, by - 4, 8, 7, METAL_HI)
        pygame.draw.rect(surf, LEAF, (cx - 5, by - 16, 10, 3))
        pygame.draw.rect(surf, METAL_HI, (cx - 3, by - 15, 6, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 10, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 7, 2, 2 if not mouth_open else 3))

    elif species_id == "thorn_beak":
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, THORN)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, THORN)
        rect_out(surf, cx - 12, by - 9 + wing_bob, 6, 10, THORN)
        rect_out(surf, cx + 6, by - 9 + wing_bob, 6, 10, THORN)
        rect_out(surf, cx - 7, by - 13, 14, 18, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 3, 6, 7))
        rect_out(surf, cx - 8, by - 18, 3, 5, THORN)
        rect_out(surf, cx + 5, by - 18, 3, 5, THORN)
        draw_eyes(surf, cx - 4, cx + 2, by - 9, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 6, 3, 3))

    elif species_id == "chrono_wing":
        rect_out(surf, cx - 14, by - 11 + hover, 7, 9, GOLD)
        rect_out(surf, cx + 7, by - 11 + hover, 7, 9, GOLD)
        pygame.draw.rect(surf, GOLD_HI, (cx - 13, by - 9 + hover, 4, 3))
        pygame.draw.rect(surf, GOLD_HI, (cx + 9, by - 9 + hover, 4, 3))
        pygame.draw.rect(surf, OUT, (cx - 6, by - 19 + hover, 12, 3))
        pygame.draw.rect(surf, GOLD_HI, (cx - 5, by - 18 + hover, 10, 1))
        rect_out(surf, cx - 7, by - 13 + hover, 14, 16, BODY)
        pygame.draw.rect(surf, GOLD, (cx - 4, by - 3 + hover, 8, 5))
        pygame.draw.rect(surf, CRYSTAL, (cx - 1, by - 2 + hover, 2, 3))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 10 + hover, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 9 + hover, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, CRYSTAL, (cx - 1, by - 5 + hover, 2, 2))

    elif species_id == "mecha_forge":
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, METAL)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, METAL)
        rect_out(surf, cx - 12, by - 13, 5, 7, METAL)
        rect_out(surf, cx + 7, by - 13, 5, 7, METAL)
        pygame.draw.rect(surf, NEON, (cx - 11, by - 12, 3, 2))
        pygame.draw.rect(surf, NEON, (cx + 8, by - 12, 3, 2))
        rect_out(surf, cx - 8, by - 10, 16, 14, BODY)
        pygame.draw.rect(surf, METAL_HI, (cx - 6, by - 4, 12, 6))
        pygame.draw.rect(surf, NEON, (cx - 2, by - 3, 4, 4))
        rect_out(surf, cx - 6, by - 16, 12, 7, METAL)
        pygame.draw.rect(surf, OUT, (cx - 5, by - 14, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 13, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 2, by - 9, 4, 2))

    elif species_id == "glitch_vex":
        gh = -2 if step in (1, 3) else 0
        rect_out(surf, cx - 14, by - 11 + gh, 5, 4, NEON)
        rect_out(surf, cx - 12, by - 5 + gh, 4, 4, LIGHT)
        rect_out(surf, cx + 9, by - 11 + gh, 5, 4, NEON)
        rect_out(surf, cx + 8, by - 5 + gh, 4, 4, LIGHT)
        rect_out(surf, cx - 7, by - 13 + gh, 14, 13, BODY)
        rect_out(surf, cx - 4, by + 0 + gh, 8, 4, LIGHT)
        pygame.draw.rect(surf, NEON, (cx - 7, by - 17 + gh, 3, 4))
        pygame.draw.rect(surf, NEON, (cx + 4, by - 17 + gh, 3, 4))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 10 + gh, 10, 5))
        draw_eyes(surf, cx - 4, cx + 2, by - 9 + gh, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 2, by - 4 + gh, 4, 2))


def make_strip(frames: int) -> pygame.Surface:
    return pygame.Surface((frames * 32, 32), pygame.SRCALPHA)


def build_species_folder(species_id: str, force: bool = False) -> None:
    out_dir = SPRITES_ROOT / species_id
    if not force and (out_dir / "idle.png").exists() and (out_dir / "bed.png").exists():
        print(f"Keeping existing sprites for '{species_id}'")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    bed = pygame.Surface((32, 32), pygame.SRCALPHA)
    draw_bed(bed)
    draw_blanket(bed, coverage=0)
    pygame.image.save(bed, str(out_dir / "bed.png"))

    sheet = make_strip(2)
    for i, dy in enumerate((0, -1)):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_creature(cell, species_id, dy=dy)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "idle.png"))

    sheet = make_strip(4)
    for i in range(4):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_creature(cell, species_id, dy=(-1 if i % 2 == 1 else 0), step=i)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "walk.png"))

    # sleep_start.png: hop beside bed -> jump in -> pull covers halfway -> tucked in
    sheet = make_strip(4)
    for i, (dx, dy, eye, cov) in enumerate((
        (-3, 0, "open", 0),
        (-1, -3, "open", 0),
        (0, 0, "closed", 1),
        (0, 0, "closed", 2),
    )):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_bed(cell)
        draw_creature(cell, species_id, dx=dx, dy=dy, eye_mode=eye)
        draw_blanket(cell, coverage=cov)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "sleep_start.png"))

   # sleep.png: tucked snugly under the covers with gentle 1px breathing
    sheet = make_strip(2)
    for i, (dy, br) in enumerate(((0, 0), (1, 1))):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_bed(cell)
        draw_creature(cell, species_id, dy=dy, eye_mode="closed")
        draw_blanket(cell, coverage=2, breathe=br)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "sleep.png"))

    # wake_up.png: tucked in -> push covers back -> hop out -> ready
    sheet = make_strip(4)
    for i, (dx, dy, eye, cov) in enumerate((
        (0, 0, "closed", 2),
        (0, 0, "open", 1),
        (-1, -3, "happy", 0),
        (-3, 0, "open", 0),
    )):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_bed(cell)
        if cov == 0:
            draw_blanket(cell, coverage=0)
            draw_creature(cell, species_id, dx=dx, dy=dy, eye_mode=eye)
        else:
            draw_creature(cell, species_id, dx=dx, dy=dy, eye_mode=eye)
            draw_blanket(cell, coverage=cov)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "wake_up.png"))

    sheet = make_strip(4)
    for i in range(4):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_creature(cell, species_id, dx=-3, dy=(1 if i % 2 == 1 else 0), mouth_open=(i % 2 == 1))
        pygame.draw.rect(cell, OUT, (21, 24, 9, 5))
        pygame.draw.rect(cell, FOOD_BOWL, (22, 25, 7, 3))
        if i < 3:
            pygame.draw.rect(cell, FOOD_FILL, (23, 23 + (i // 2), 5, 2))
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "eat.png"))

    sheet = make_strip(4)
    for i in range(4):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_creature(
            cell,
            species_id,
            dx=-2,
            dy=(-2 if i == 3 else 0),
            eye_mode=("happy" if i == 3 else "open"),
            mouth_open=(i in (1, 2)),
        )
        if i < 3:
            sx, sy = 25 - i * 2, 16 + i * 2
            pygame.draw.rect(cell, GOLD, (sx, sy - 1, 3, 5))
            pygame.draw.rect(cell, GOLD, (sx - 1, sy, 5, 3))
            pygame.draw.rect(cell, GOLD_HI, (sx + 1, sy + 1, 1, 1))
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "snack.png"))

    sheet = make_strip(4)
    for i, (by_ball, dy) in enumerate(((22, 0), (14, -2), (18, -1), (22, 0))):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_creature(cell, species_id, dx=-3, dy=dy, eye_mode="happy")
        pygame.draw.circle(cell, OUT, (25, by_ball), 4)
        pygame.draw.circle(cell, BALL_COL, (25, by_ball), 3)
        cell.set_at((24, by_ball - 1), BALL_HI)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "play.png"))

    sheet = make_strip(4)
    for i, dy in enumerate((0, -4, -2, 0)):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_creature(cell, species_id, dy=dy, eye_mode="happy")
        if i in (1, 2):
            pygame.draw.rect(cell, GOLD, (4, 5, 2, 2))
            pygame.draw.rect(cell, GOLD, (26, 6, 2, 2))
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "happy.png"))

    print(f"Generated 10 sprites for '{species_id}' -> {out_dir}")


def main() -> None:
    force_all = "--force-all" in sys.argv
    all_species = [
        # 5 Babies
        "spark_kit", "cinder_pup", "aqua_fin", "sprout_owl", "cog_bit",
        # 15 Teens (Radiant, Trained, Wild)
        "star_lynx", "jolt_kat", "feral_volt",
        "sun_pup", "blaze_hound", "char_fang",
        "reef_kin", "wave_crest", "murk_fin",
        "petal_owl", "bark_wing", "bramblet",
        "gild_bot", "gear_unit", "static_bit",
        # 15 Adults (Radiant, Trained, Wild)
        "aether_cat", "volt_lynx", "storm_claw",
        "sol_hound", "pyro_fang", "ash_maw",
        "coral_shell", "tide_drake", "abyss_fin",
        "bloom_wing", "iron_bark", "thorn_beak",
        "chrono_wing", "mecha_forge", "glitch_vex",
    ]
    for sid in all_species:
        build_species_folder(sid, force=(force_all if sid == "spark_kit" else True))


if __name__ == "__main__":
    main()