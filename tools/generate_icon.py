"""Generates a 256x256 borderless PNG icon for CardputerZero Store & APPLaunch."""

from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent.parent
SPRITE_PATH = ROOT / "assets" / "sprites" / "spark_kit" / "happy.png"
OUT_PATH = ROOT / "assets" / "images" / "z_pet_icon.png"

SIZE = 256
BG_TOP    = (34, 22, 58, 255)
BG_BOTTOM = (58, 38, 96, 255)
FLOOR     = (28, 18, 46, 255)
GLOW      = (255, 236, 128, 255)
STAR_SOFT = (196, 162, 255, 255)


def main() -> None:
    if not SPRITE_PATH.exists():
        raise FileNotFoundError(
            f"Missing {SPRITE_PATH}. Run 'python tools/generate_placeholders.py' first."
        )

    icon = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

    # Full-bleed vertical gradient background (no rounded corners or outer border)
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = (
            int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t),
            int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t),
            int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t),
            255,
        )
        pygame.draw.line(icon, color, (0, y), (SIZE - 1, y))

    # Subtle ground shadow
    pygame.draw.ellipse(icon, FLOOR, (46, 188, 164, 30))

    # Slice frame 0 (32x32) from happy.png and scale 6x (192x192) crisply
    sheet = pygame.image.load(str(SPRITE_PATH))
    frame = sheet.subsurface(pygame.Rect(0, 0, 32, 32)).copy()
    scaled = pygame.transform.scale(frame, (192, 192))
    icon.blit(scaled, ((SIZE - 192) // 2, 34))

    # Pixel sparkles
    for sx, sy, s, col in [
        (36, 44, 10, GLOW),
        (206, 52, 10, GLOW),
        (46, 152, 8, STAR_SOFT),
        (202, 140, 8, STAR_SOFT),
    ]:
        pygame.draw.rect(icon, col, (sx, sy, s, s))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(icon, str(OUT_PATH))
    print(f"Generated 256x256 borderless icon at: {OUT_PATH}")


if __name__ == "__main__":
    main()