from pathlib import Path
import pygame

# Exact RGBA colors drawn in tools/generate_placeholders.py
BASE_SOURCE_COLORS = {
    "body":  (145, 98, 225, 255),
    "light": (196, 162, 255, 255),
    "belly": (240, 232, 255, 255),
    "eye":   (255, 236, 110, 255),
}

# 7 selectable base coats (Yellow & White get high-contrast eye colors)
PET_COLOR_PALETTES = {
    "purple": {
        "label": "Purple",
        "swatch": (145, 98, 225),
        "body":  (145, 98, 225, 255),
        "light": (196, 162, 255, 255),
        "belly": (240, 232, 255, 255),
        "eye":   (255, 236, 110, 255),
    },
    "red": {
        "label": "Red",
        "swatch": (215, 68, 78),
        "body":  (215, 68, 78, 255),
        "light": (248, 128, 134, 255),
        "belly": (255, 228, 224, 255),
        "eye":   (255, 236, 110, 255),
    },
    "yellow": {
        "label": "Yellow",
        "swatch": (232, 186, 52),
        "body":  (232, 186, 52, 255),
        "light": (255, 226, 112, 255),
        "belly": (255, 248, 214, 255),
        "eye":   (72, 198, 245, 255),
    },
    "white": {
        "label": "White",
        "swatch": (236, 240, 248),
        "body":  (222, 226, 238, 255),
        "light": (250, 252, 255, 255),
        "belly": (196, 212, 236, 255),
        "eye":   (148, 108, 245, 255),
    },
    "green": {
        "label": "Green",
        "swatch": (74, 182, 108),
        "body":  (74, 182, 108, 255),
        "light": (138, 228, 158, 255),
        "belly": (228, 250, 224, 255),
        "eye":   (255, 236, 110, 255),
    },
    "pink": {
        "label": "Pink",
        "swatch": (235, 116, 178),
        "body":  (235, 116, 178, 255),
        "light": (255, 174, 216, 255),
        "belly": (255, 236, 246, 255),
        "eye":   (255, 236, 110, 255),
    },
    "blue": {
        "label": "Blue",
        "swatch": (74, 134, 232),
        "body":  (74, 134, 232, 255),
        "light": (136, 188, 255, 255),
        "belly": (226, 242, 255, 255),
        "eye":   (255, 236, 110, 255),
    },
}

PET_COLOR_ORDER = ["purple", "red", "yellow", "white", "green", "pink", "blue"]


def recolor_surface(surface: pygame.Surface, color_id: str) -> pygame.Surface:
    """Swaps only the pet's base coat pixels, leaving props and outlines untouched."""
    if color_id == "purple" or color_id not in PET_COLOR_PALETTES:
        return surface

    palette = PET_COLOR_PALETTES[color_id]
    recolored = surface.copy()
    pa = pygame.PixelArray(recolored)
    for key, src_rgba in BASE_SOURCE_COLORS.items():
        dst_rgba = palette[key]
        if src_rgba != dst_rgba:
            pa.replace(recolored.map_rgb(src_rgba), recolored.map_rgb(dst_rgba))
    del pa
    return recolored


class Animation:
    """Holds sliced frames and playback timing for a single sprite strip."""

    def __init__(self, frames: list[pygame.Surface], fps: float = 6.0, loop: bool = True):
        self.frames = frames
        self.flipped_frames = [
            pygame.transform.flip(frame, True, False) for frame in frames
        ]
        self.frame_duration = 1.0 / fps
        self.loop = loop

    @classmethod
    def from_sprite_sheet(
        cls,
        path: Path,
        frame_w: int = 32,
        frame_h: int = 32,
        scale: int = 2,
        fps: float = 6.0,
        loop: bool = True,
        color_id: str = "purple",
    ) -> "Animation":
        sheet = pygame.image.load(str(path)).convert_alpha()
        sheet = recolor_surface(sheet, color_id)

        frame_count = sheet.get_width() // frame_w
        if frame_count < 1:
            raise ValueError(f"Sprite sheet '{path}' is narrower than {frame_w}px.")

        frames: list[pygame.Surface] = []
        target_size = (frame_w * scale, frame_h * scale)

        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            cell = sheet.subsurface(rect).copy()
            scaled = pygame.transform.scale(cell, target_size)
            frames.append(scaled)

        return cls(frames=frames, fps=fps, loop=loop)


class Animator:
    """State controller that advances frames and chains one-shot transitions cleanly."""

    def __init__(self, animations: dict[str, Animation], default_name: str = "idle"):
        if default_name not in animations:
            raise KeyError(f"Default animation '{default_name}' not found.")

        self.animations = animations
        self.default_name = default_name
        self.current_name = default_name
        self.next_name = default_name
        self.frame_index = 0
        self.timer = 0.0
        self.facing_left = False

    @property
    def is_playing_oneshot(self) -> bool:
        return not self.animations[self.current_name].loop

    def play(self, name: str, restart: bool = False, next_anim: str | None = None) -> None:
        if name not in self.animations:
            return
        if name != self.current_name or restart:
            self.current_name = name
            self.frame_index = 0
            self.timer = 0.0
            self.next_name = next_anim if next_anim in self.animations else self.default_name
        elif next_anim in self.animations:
            self.next_name = next_anim

    def update(self, dt: float) -> None:
        anim = self.animations[self.current_name]
        self.timer += dt

        while self.timer >= anim.frame_duration:
            self.timer -= anim.frame_duration
            self.frame_index += 1

            if self.frame_index >= len(anim.frames):
                if anim.loop:
                    self.frame_index = 0
                else:
                    follow_up = self.next_name
                    self.play(follow_up, restart=True)
                    break

    def get_frame(self) -> pygame.Surface:
        anim = self.animations[self.current_name]
        frames = anim.flipped_frames if self.facing_left else anim.frames
        return frames[self.frame_index]


def load_species_animations(
    species_dir: Path,
    frame_w: int = 32,
    frame_h: int = 32,
    scale: int = 2,
    color_id: str = "purple",
) -> Animator:
    """Loads the standard animation set for any pet species folder."""
    manifest = {
        "idle":        ("idle.png",        4.0, True),
        "walk":        ("walk.png",        8.0, True),
        "sleep_start": ("sleep_start.png", 6.0, False),
        "sleep":       ("sleep.png",       2.5, True),
        "wake_up":     ("wake_up.png",     6.0, False),
        "eat":         ("eat.png",         6.0, False),
        "snack":       ("snack.png",       7.0, False),
        "play":        ("play.png",        8.0, False),
        "happy":       ("happy.png",       8.0, False),
    }

    loaded: dict[str, Animation] = {}
    for name, (filename, fps, loop) in manifest.items():
        file_path = species_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing sprite sheet: {file_path}\n"
                "Run 'python tools/generate_placeholders.py' first!"
            )
        loaded[name] = Animation.from_sprite_sheet(
            file_path,
            frame_w=frame_w,
            frame_h=frame_h,
            scale=scale,
            fps=fps,
            loop=loop,
            color_id=color_id,
        )

    return Animator(loaded, default_name="idle")