from pathlib import Path
import platform

# --- Paths (always relative so the game works on Windows and Cardputer Zero) ---
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
DATA_DIR = BASE_DIR / "data"

# Future-proof save folder (installed Linux .deb apps can't write inside /usr/share)
SAVE_DIR = Path.home() / ".config" / "z-pet"

# --- Display & Performance ---
LOGICAL_WIDTH = 320
LOGICAL_HEIGHT = 170
PC_SCALE = 3          # 960x510 preview window on Windows
SPRITE_SIZE = 32      # Native pixel-art cell size (32x32)
SPRITE_SCALE = 2      # Rendered at 64x64 on the 320x170 canvas
FPS = 30              # Smooth animation while keeping CM0 cool and battery-friendly

# Automatically switch to fullscreen when running on ARM Linux (Cardputer Zero)
IS_HANDHELD = platform.system() == "Linux" and platform.machine() in ("aarch64", "armv7l")

# --- Z-Pet Color Palette ---
COLOR_BG = (24, 18, 36)          # Deep obsidian purple
COLOR_FLOOR = (42, 32, 62)       # Room floor
COLOR_PANEL = (34, 26, 52)       # Top/bottom HUD bars
COLOR_ACCENT = (178, 136, 255)   # Lavender border & highlights
COLOR_TEXT = (242, 238, 252)     # Crisp off-white text
COLOR_MUTED = (155, 145, 180)    # Secondary hints