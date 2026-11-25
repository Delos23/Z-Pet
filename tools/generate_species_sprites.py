"""Generates 32x32 pixel-art sprite sheets for all 5 starters & 15 care evolutions.

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
FOOD_BOWL = (198, 86, 114, 255)
FOOD_FILL = (232, 168, 92, 255)
BALL_COL  = (242, 92, 132, 255)
BALL_HI   = (255, 198, 214, 255)
BED_RIM   = (92, 58, 136, 255)
BED_PAD   = (156, 112, 214, 255)
BED_TRIM  = (224, 196, 255, 255)


def rect_out(surf: pygame.Surface, x: int, y: int, w: int, h: int, fill: tuple) -> None:
    pygame.draw.rect(surf, OUT, (x - 1, y - 1, w + 2, h + 2))
    pygame.draw.rect(surf, fill, (x, y, w, h))


def draw_bed(surf: pygame.Surface) -> None:
    pygame.draw.rect(surf, OUT, (3, 21, 26, 9))
    pygame.draw.rect(surf, BED_RIM, (4, 22, 24, 7))
    pygame.draw.rect(surf, BED_PAD, (6, 23, 20, 4))
    pygame.draw.rect(surf, BED_TRIM, (6, 22, 20, 1))
    pygame.draw.rect(surf, OUT, (21, 18, 7, 5))
    pygame.draw.rect(surf, BED_TRIM, (22, 19, 5, 3))


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

    # ===================== 5 STARTERS =====================
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
        # Plump forest baby owl with twin leaf-sprouts on head & little wings
        rect_out(surf, cx - 4, by + 5 + leg_l, 3, 2, GOLD)
        rect_out(surf, cx + 1, by + 5 + leg_r, 3, 2, GOLD)
        # Round owl body + side wings
        rect_out(surf, cx - 8, by - 4 + wing_bob, 3, 7, LIGHT)
        rect_out(surf, cx + 5, by - 4 + wing_bob, 3, 7, LIGHT)
        rect_out(surf, cx - 6, by - 9, 12, 15, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 4, by - 1, 8, 6))
        # Leaf sprout antenna on top of head
        pygame.draw.rect(surf, OUT, (cx - 1, by - 13, 2, 4))
        pygame.draw.rect(surf, LEAF, (cx - 5, by - 15, 4, 3))
        pygame.draw.rect(surf, LEAF_HI, (cx + 1, by - 15, 4, 3))
        # Owl eyes + little gold beak
        draw_eyes(surf, cx - 4, cx + 2, by - 6, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 3, 2, 2 if not mouth_open else 3))

    elif species_id == "cog_bit":
        # Compact floating clockwork bat-bot with gear ears & pixel visor
        hover = -1 if step in (1, 3) else 0
        # Mechanical bat wings
        rect_out(surf, cx - 12, by - 7 + hover, 5, 6, METAL)
        rect_out(surf, cx + 7, by - 7 + hover, 5, 6, METAL)
        pygame.draw.rect(surf, NEON, (cx - 11, by - 5 + hover, 3, 2))
        pygame.draw.rect(surf, NEON, (cx + 8, by - 5 + hover, 3, 2))
        # Antenna gear on top
        pygame.draw.rect(surf, OUT, (cx - 1, by - 14 + hover, 2, 4))
        pygame.draw.rect(surf, GOLD, (cx - 2, by - 16 + hover, 4, 3))
        # Metallic-trimmed spherical chassis
        rect_out(surf, cx - 7, by - 9 + hover, 14, 12, BODY)
        pygame.draw.rect(surf, METAL, (cx - 7, by - 1 + hover, 14, 3))
        pygame.draw.rect(surf, LIGHT, (cx - 5, by - 9 + hover, 10, 2))
        # Visor eyes
        pygame.draw.rect(surf, OUT, (cx - 5, by - 7 + hover, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 6 + hover, eye_mode)
        # Little thruster feet
        rect_out(surf, cx - 4, by + 3 + hover, 3, 2, METAL)
        rect_out(surf, cx + 1, by + 3 + hover, 3, 2, METAL)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 1, by - 2 + hover, 2, 2))

    # ===================== SPARKKIT EVOLUTIONS =====================
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
        # Wild spiky feral thunder panther with jagged shoulder spikes & big claws
        rect_out(surf, cx - 13, by - 11, 5, 4, NEON)
        rect_out(surf, cx - 10, by - 7, 4, 4, BODY)
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, BODY)
        pygame.draw.rect(surf, GOLD_HI, (cx + 6, by + 6 + leg_r, 2, 2))  # Claws
        rect_out(surf, cx - 8, by - 7, 16, 11, BODY)
        pygame.draw.rect(surf, NEON, (cx - 6, by - 9, 4, 3))  # Back spikes
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 3, 7, 6))
        rect_out(surf, cx - 6, by - 15, 13, 9, BODY)
        rect_out(surf, cx - 8, by - 17, 4, 4, LIGHT)  # Swept ears
        rect_out(surf, cx + 4, by - 17, 4, 4, LIGHT)
        draw_eyes(surf, cx - 3, cx + 3, by - 11, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, GOLD_HI, (cx, by - 7, 3, 2))

    # ===================== CINDERPUP EVOLUTIONS =====================
    elif species_id == "sol_hound":
        # Noble sun-maned hound with glowing golden crest
        rect_out(surf, cx - 12, by - 9, 5, 5, GOLD_HI)
        rect_out(surf, cx - 6, by + 3 + leg_l, 3, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 3, 5, BODY)
        rect_out(surf, cx - 7, by - 6, 15, 10, BODY)
        # Golden sun mane around chest
        rect_out(surf, cx - 4, by - 8, 12, 7, GOLD)
        pygame.draw.rect(surf, GOLD_HI, (cx - 2, by - 7, 8, 3))
        rect_out(surf, cx - 5, by - 15, 12, 9, BODY)
        rect_out(surf, cx + 5, by - 10, 4, 4, LIGHT)
        pygame.draw.rect(surf, GOLD_HI, (cx - 1, by - 18, 4, 3))  # Sun crest
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
        # Heavy rogue cinder beast with metal jaw guard & smoking spine
        rect_out(surf, cx - 13, by - 6, 6, 4, METAL)
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, BODY)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, BODY)
        rect_out(surf, cx - 8, by - 7, 17, 11, BODY)
        pygame.draw.rect(surf, EMBER, (cx - 7, by - 10, 4, 3))
        pygame.draw.rect(surf, EMBER, (cx - 1, by - 10, 4, 3))
        rect_out(surf, cx - 5, by - 15, 13, 9, BODY)
        rect_out(surf, cx + 4, by - 9, 6, 4, METAL_HI)  # Iron jaw
        draw_eyes(surf, cx - 2, cx + 4, by - 12, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, EMBER, (cx + 5, by - 7, 3, 2))

    # ===================== AQUAFIN EVOLUTIONS =====================
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
        # Deep-sea angler predator with glowing lure & jagged fins
        rect_out(surf, cx - 13, by - 5, 6, 6, BODY)
        pygame.draw.rect(surf, NEON, (cx - 13, by - 4, 2, 4))
        rect_out(surf, cx - 6, by + 4 + leg_l, 3, 4, BODY)
        rect_out(surf, cx + 3, by + 4 + leg_r, 3, 4, BODY)
        rect_out(surf, cx - 7, by - 8, 15, 13, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 2, by - 2, 8, 6))
        # Angler lure arcing over head
        pygame.draw.rect(surf, OUT, (cx + 1, by - 16, 2, 8))
        pygame.draw.rect(surf, OUT, (cx + 3, by - 16, 4, 2))
        pygame.draw.rect(surf, NEON, (cx + 6, by - 14, 3, 3))
        draw_eyes(surf, cx - 2, cx + 4, by - 6, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, GOLD_HI, (cx + 2, by - 1, 5, 2))

    # ===================== SPROUTOWL EVOLUTIONS =====================
    elif species_id == "bloom_wing":
        # Majestic blossom owl with wide floral wings & pink petal crown
        rect_out(surf, cx - 4, by + 4 + leg_l, 3, 4, GOLD)
        rect_out(surf, cx + 1, by + 4 + leg_r, 3, 4, GOLD)
        rect_out(surf, cx - 13, by - 9 + wing_bob, 6, 11, LEAF)
        rect_out(surf, cx + 7, by - 9 + wing_bob, 6, 11, LEAF)
        pygame.draw.rect(surf, FLOWER, (cx - 12, by - 8 + wing_bob, 3, 3))
        pygame.draw.rect(surf, FLOWER, (cx + 9, by - 8 + wing_bob, 3, 3))
        rect_out(surf, cx - 7, by - 13, 14, 18, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 4, by - 4, 8, 8))
        # Blossom crown
        pygame.draw.rect(surf, LEAF_HI, (cx - 5, by - 16, 10, 3))
        pygame.draw.rect(surf, FLOWER, (cx - 2, by - 18, 4, 4))
        pygame.draw.rect(surf, GOLD_HI, (cx - 1, by - 17, 2, 2))
        draw_eyes(surf, cx - 4, cx + 2, by - 9, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 6, 2, 2 if not mouth_open else 3))

    elif species_id == "iron_bark":
        # Armored guardian tree-owl with steel shoulder pauldrons & shield chest
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
        # Fierce horned bramble owl with jagged thorn wings
        rect_out(surf, cx - 5, by + 4 + leg_l, 3, 4, THORN)
        rect_out(surf, cx + 2, by + 4 + leg_r, 3, 4, THORN)
        rect_out(surf, cx - 12, by - 9 + wing_bob, 6, 10, THORN)
        rect_out(surf, cx + 6, by - 9 + wing_bob, 6, 10, THORN)
        rect_out(surf, cx - 7, by - 13, 14, 18, BODY)
        pygame.draw.rect(surf, BELLY, (cx - 3, by - 3, 6, 7))
        # Sharp horn tufts
        rect_out(surf, cx - 8, by - 18, 3, 5, THORN)
        rect_out(surf, cx + 5, by - 18, 3, 5, THORN)
        draw_eyes(surf, cx - 4, cx + 2, by - 9, eye_mode)
        pygame.draw.rect(surf, GOLD, (cx - 1, by - 6, 3, 3))

    # ===================== COGBIT EVOLUTIONS =====================
    elif species_id == "chrono_wing":
        # Gilded clockwork seraph with wide golden gear-wings & halo ring
        hover = -1 if step in (1, 3) else 0
        rect_out(surf, cx - 14, by - 11 + hover, 7, 9, GOLD)
        rect_out(surf, cx + 7, by - 11 + hover, 7, 9, GOLD)
        pygame.draw.rect(surf, GOLD_HI, (cx - 13, by - 9 + hover, 4, 3))
        pygame.draw.rect(surf, GOLD_HI, (cx + 9, by - 9 + hover, 4, 3))
        # Clock-ring halo
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
        # Heavy bipedal cyber-mech with shoulder cannons & chest core
        rect_out(surf, cx - 7, by + 3 + leg_l, 4, 5, METAL)
        rect_out(surf, cx + 3, by + 3 + leg_r, 4, 5, METAL)
        # Shoulder pods
        rect_out(surf, cx - 12, by - 13, 5, 7, METAL)
        rect_out(surf, cx + 7, by - 13, 5, 7, METAL)
        pygame.draw.rect(surf, NEON, (cx - 11, by - 12, 3, 2))
        pygame.draw.rect(surf, NEON, (cx + 8, by - 12, 3, 2))
        # Armored torso + head
        rect_out(surf, cx - 8, by - 10, 16, 14, BODY)
        pygame.draw.rect(surf, METAL_HI, (cx - 6, by - 4, 12, 6))
        pygame.draw.rect(surf, NEON, (cx - 2, by - 3, 4, 4))
        rect_out(surf, cx - 6, by - 16, 12, 7, METAL)
        pygame.draw.rect(surf, OUT, (cx - 5, by - 14, 10, 4))
        draw_eyes(surf, cx - 4, cx + 2, by - 13, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 2, by - 9, 4, 2))

    elif species_id == "glitch_vex":
        # Floating rogue static phantom with split pixel wings & neon visor
        hover = -2 if step in (1, 3) else 0
        # Split jagged glitch-wings
        rect_out(surf, cx - 14, by - 11 + hover, 5, 4, NEON)
        rect_out(surf, cx - 12, by - 5 + hover, 4, 4, LIGHT)
        rect_out(surf, cx + 9, by - 11 + hover, 5, 4, NEON)
        rect_out(surf, cx + 8, by - 5 + hover, 4, 4, LIGHT)
        # Tapered phantom chassis
        rect_out(surf, cx - 7, by - 13 + hover, 14, 13, BODY)
        rect_out(surf, cx - 4, by + 0 + hover, 8, 4, LIGHT)
        # Glitch pixel horns
        pygame.draw.rect(surf, NEON, (cx - 7, by - 17 + hover, 3, 4))
        pygame.draw.rect(surf, NEON, (cx + 4, by - 17 + hover, 3, 4))
        pygame.draw.rect(surf, OUT, (cx - 5, by - 10 + hover, 10, 5))
        draw_eyes(surf, cx - 4, cx + 2, by - 9 + hover, eye_mode)
        if mouth_open:
            pygame.draw.rect(surf, NEON, (cx - 2, by - 4 + hover, 4, 2))


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

    sheet = make_strip(4)
    for i, (dx, dy, eye) in enumerate(((-3, 0, "open"), (-1, -3, "open"), (0, -1, "closed"), (0, 1, "closed"))):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_bed(cell)
        draw_creature(cell, species_id, dx=dx, dy=dy, eye_mode=eye)
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "sleep_start.png"))

    sheet = make_strip(2)
    for i, dy in enumerate((1, 2)):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_bed(cell)
        draw_creature(cell, species_id, dy=dy, eye_mode="closed")
        sheet.blit(cell, (i * 32, 0))
    pygame.image.save(sheet, str(out_dir / "sleep.png"))

    sheet = make_strip(4)
    for i, (dx, dy, eye) in enumerate(((0, 1, "closed"), (0, -1, "open"), (-1, -3, "happy"), (-3, 0, "open"))):
        cell = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_bed(cell)
        draw_creature(cell, species_id, dx=dx, dy=dy, eye_mode=eye)
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
        # 5 Starters
        "spark_kit", "cinder_pup", "aqua_fin", "sprout_owl", "cog_bit",
        # Sparkkit evolutions
        "aether_cat", "volt_lynx", "storm_claw",
        # Cinderpup evolutions
        "sol_hound", "pyro_fang", "ash_maw",
        # Aquafin evolutions
        "coral_shell", "tide_drake", "abyss_fin",
        # Sproutowl evolutions
        "bloom_wing", "iron_bark", "thorn_beak",
        # Cogbit evolutions
        "chrono_wing", "mecha_forge", "glitch_vex",
    ]
    for sid in all_species:
        build_species_folder(sid, force=(force_all if sid == "spark_kit" else True))


if __name__ == "__main__":
    main()