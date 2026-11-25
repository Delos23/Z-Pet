"""Generates a 100x100 RGBA PNG launcher icon for Cardputer Zero APPLaunch."""

from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent.parent
SPRITE_PATH = ROOT / "assets" / "sprites" / "spark_kit" / "happy.png"
OUT_PATH = ROOT / "assets" / "ui" / "z-pet-icon.png"

SIZE = 100
BG_OUTER = (28, 18, 46, 255)
BG_INNER = (52, 34, 86, 255)
BORDER   = (178, 136, 255, 255)
GLOW     = (255, 236, 128, 255)
FLOOR    = (38, 26, 62, 255)


def main() -> None:
    if not SPRITE_PATH.exists():
        raise FileNotFoundError(
            f"Missing {SPRITE_PATH}. Run 'python tools/generate_placeholders.py' first."
        )

    icon = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

    # Rounded obsidian-purple app badge
    pygame.draw.rect(icon, BG_OUTER, (2, 2, SIZE - 4, SIZE - 4), border_radius=20)
    pygame.draw.rect(icon, BG_INNER, (8, 8, SIZE - 16, SIZE - 16), border_radius=15)
    pygame.draw.rect(icon, BORDER, (2, 2, SIZE - 4, SIZE - 4), width=4, border_radius=20)

    # Subtle ground shadow inside badge
    pygame.draw.ellipse(icon, FLOOR, (22, 70, 56, 12))

    # Slice frame 0 (32x32) from happy.png and scale 2x (64x64) crisply
    sheet = pygame.image.load(str(SPRITE_PATH))
    frame = sheet.subsurface(pygame.Rect(0, 0, 32, 32)).copy()
    scaled = pygame.transform.scale(frame, (64, 64))
    icon.blit(scaled, ((SIZE - 64) // 2, 16))

    # Corner pixel sparkles
    for sx, sy in [(18, 20), (78, 22), (22, 62)]:
        pygame.draw.rect(icon, GLOW, (sx, sy, 4, 4))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(icon, str(OUT_PATH))
    print(f"Generated 100x100 launcher icon at: {OUT_PATH}")


if __name__ == "__main__":
    main()