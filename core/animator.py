from pathlib import Path
import pygame


class Animation:
    """Holds sliced frames and playback timing for a single sprite strip."""

    def __init__(self, frames: list[pygame.Surface], fps: float = 6.0, loop: bool = True):
        self.frames = frames
        # Pre-flip once on load to save CPU cycles on the Cardputer Zero (CM0)
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
    ) -> "Animation":
        sheet = pygame.image.load(str(path)).convert_alpha()
        frame_count = sheet.get_width() // frame_w
        if frame_count < 1:
            raise ValueError(f"Sprite sheet '{path}' is narrower than {frame_w}px.")

        frames: list[pygame.Surface] = []
        target_size = (frame_w * scale, frame_h * scale)

        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            cell = sheet.subsurface(rect).copy()
            # pygame.transform.scale uses nearest-neighbor scaling (keeps pixel art sharp)
            scaled = pygame.transform.scale(cell, target_size)
            frames.append(scaled)

        return cls(frames=frames, fps=fps, loop=loop)


class Animator:
    """State controller that advances frames using delta time (dt)."""

    def __init__(self, animations: dict[str, Animation], default_name: str = "idle"):
        if default_name not in animations:
            raise KeyError(f"Default animation '{default_name}' not found.")

        self.animations = animations
        self.default_name = default_name
        self.current_name = default_name
        self.frame_index = 0
        self.timer = 0.0
        self.facing_left = False

    @property
    def is_playing_oneshot(self) -> bool:
        return not self.animations[self.current_name].loop

    def play(self, name: str, restart: bool = False) -> None:
        if name not in self.animations:
            return
        if name != self.current_name or restart:
            self.current_name = name
            self.frame_index = 0
            self.timer = 0.0

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
                    # One-shot finished -> snap back to idle
                    self.play(self.default_name, restart=True)
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
) -> Animator:
    """Loads the standard animation set for any pet species folder."""
    manifest = {
        "idle":  ("idle.png",  4.0, True),
        "walk":  ("walk.png",  8.0, True),
        "eat":   ("eat.png",   5.0, False),
        "happy": ("happy.png", 8.0, False),
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
            file_path, frame_w=frame_w, frame_h=frame_h, scale=scale, fps=fps, loop=loop
        )

    return Animator(loaded, default_name="idle")