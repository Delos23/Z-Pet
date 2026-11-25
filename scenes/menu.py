"""Start-Up Title, New Pet (Custom Name + Base Color), and Settings scenes."""

import math
import random
import pygame

import settings
from core.animator import PET_COLOR_ORDER, PET_COLOR_PALETTES, load_species_animations
from core.save_manager import (
    create_new_pet,
    get_save_preview,
    has_save,
    load_pet,
    save_config,
)

SEL_FILL = (76, 52, 122)
DISABLED_TEXT = (96, 86, 122)
WARN_COLOR = (245, 195, 85)
GOOD_COLOR = (105, 225, 145)
STAR_BRIGHT = (245, 240, 255)
STAR_DIM = (128, 112, 178)

SKY_OPTIONS = [
    ("auto", "Auto"),
    ("dawn", "Dawn"),
    ("day", "Day"),
    ("sunset", "Sunset"),
    ("night", "Night"),
]

SPEED_OPTIONS = [
    (1.0, "1x Normal"),
    (10.0, "10x Fast"),
    (60.0, "60x Test"),
]


def _make_stars(count: int = 24) -> list[tuple[int, int, float]]:
    rng = random.Random(42)
    return [
        (rng.randint(4, settings.LOGICAL_WIDTH - 4), rng.randint(4, 140), rng.uniform(0, 6.28))
        for _ in range(count)
    ]


def _draw_starfield(canvas: pygame.Surface, stars: list[tuple[int, int, float]], elapsed: float) -> None:
    canvas.fill(settings.COLOR_BG)
    for sx, sy, phase in stars:
        twinkle = math.sin(elapsed * 2.4 + phase)
        col = STAR_BRIGHT if twinkle > 0.35 else STAR_DIM
        size = 2 if twinkle > 0.7 else 1
        canvas.fill(col, (sx, sy, size, size))


def _draw_footer(canvas: pygame.Surface, font_sans: pygame.font.Font, text: str) -> None:
    pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
    surf = font_sans.render(text, True, settings.COLOR_MUTED)
    canvas.blit(surf, ((settings.LOGICAL_WIDTH - surf.get_width()) // 2, 152))


class TitleScene:
    """Main Start-Up menu: Continue, New Pet, Settings, Quit."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict):
        self.fonts = fonts
        self.config = config
        self.stars = _make_stars(26)
        self.elapsed = 0.0
        self.hop_timer = 3.2

        self.save_exists = has_save()
        self.preview = get_save_preview() if self.save_exists else None

        self.items = [
            ("continue", "Continue"),
            ("new_pet", "New Pet"),
            ("settings", "Settings"),
            ("quit", "Quit"),
        ]
        self.cursor = 0 if self.save_exists else 1

        preview_color = self.preview["color"] if self.preview else "purple"
        sprite_dir = settings.SPRITES_DIR / "spark_kit"
        self.animator = load_species_animations(
            sprite_dir,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=preview_color,
        )
        self.animator.play("idle", restart=True)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.cursor = (self.cursor - 1) % len(self.items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.cursor = (self.cursor + 1) % len(self.items)
        elif event.key in (pygame.K_ESCAPE, pygame.K_q):
            return ("quit", {})
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            action = self.items[self.cursor][0]
            if action == "continue":
                if not self.save_exists:
                    self.cursor = 1
                    return None
                pet, offline = load_pet(time_scale=float(self.config.get("time_scale", 1.0)))
                return ("home", {"pet": pet, "offline": offline})
            if action == "new_pet":
                return ("new_pet", {})
            if action == "settings":
                return ("settings", {})
            if action == "quit":
                return ("quit", {})
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.hop_timer -= dt
        if self.hop_timer <= 0:
            self.animator.play("happy", restart=True, next_anim="idle")
            self.hop_timer = random.uniform(4.0, 6.5)
        self.animator.update(dt)

    def render(self, canvas: pygame.Surface) -> None:
        _draw_starfield(canvas, self.stars, self.elapsed)

        title_shadow = self.fonts["title"].render("Z-PET", True, (18, 10, 34))
        title_surf = self.fonts["title"].render("Z-PET", True, settings.COLOR_TEXT)
        title_x = (146 - title_surf.get_width()) // 2
        canvas.blit(title_shadow, (title_x + 2, 13))
        canvas.blit(title_surf, (title_x, 11))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (24, 38), (122, 38), 2)

        pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(48, 110, 50, 10))
        canvas.blit(self.animator.get_frame(), (41, 52))

        if self.preview:
            info_txt = f"{self.preview['name']} ({self.preview['age_hours']}h)"
            info_col = settings.COLOR_ACCENT if self.preview["alive"] else WARN_COLOR
        else:
            info_txt = "No pet saved yet"
            info_col = settings.COLOR_MUTED
        info_surf = self.fonts["sans"].render(info_txt, True, info_col)
        canvas.blit(info_surf, ((146 - info_surf.get_width()) // 2, 124))

        panel_rect = pygame.Rect(150, 12, 160, 124)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, panel_rect, border_radius=6)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, panel_rect, 1, border_radius=6)

        for idx, (action, label) in enumerate(self.items):
            row_y = 20 + idx * 28
            row_rect = pygame.Rect(158, row_y, 144, 24)
            is_selected = idx == self.cursor
            is_disabled = action == "continue" and not self.save_exists

            if is_selected:
                pygame.draw.rect(canvas, SEL_FILL, row_rect, border_radius=4)
                pygame.draw.rect(canvas, settings.COLOR_ACCENT, row_rect, 1, border_radius=4)

            if is_disabled:
                text_col = DISABLED_TEXT
                display_lbl = "Continue (--)"
            elif is_selected:
                text_col = settings.COLOR_TEXT
                display_lbl = label
            else:
                text_col = settings.COLOR_MUTED
                display_lbl = label

            if is_selected:
                arrow = self.fonts["mono"].render(">", True, GOOD_COLOR if not is_disabled else DISABLED_TEXT)
                canvas.blit(arrow, (164, row_y + 4))

            lbl_surf = self.fonts["sans"].render(display_lbl, True, text_col)
            canvas.blit(lbl_surf, (178, row_y + 4))

        _draw_footer(canvas, self.fonts["sans"], "Up/Dn:Move  Enter:Select  Esc:Quit")


class NewPetScene:
    """Hatch a new pet: choose a Base Color and enter a custom name (or keep SPARKKIT)."""

    accepts_text_input = True

    def __init__(self, fonts: dict, config: dict):
        self.fonts = fonts
        self.config = config
        self.stars = _make_stars(20)
        self.elapsed = 0.0

        self.custom_name = ""   # Blank keeps the default SPARKKIT
        self.color_idx = 0      # Starts on Purple
        self.focus = "name"     # "name" or "color"
        self.will_overwrite = has_save()

        self._sprite_dir = settings.SPRITES_DIR / "spark_kit"
        self._load_preview_animator(play_happy=True)

    @property
    def selected_color_id(self) -> str:
        return PET_COLOR_ORDER[self.color_idx]

    def _load_preview_animator(self, play_happy: bool = False) -> None:
        self.animator = load_species_animations(
            self._sprite_dir,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=self.selected_color_id,
        )
        if play_happy:
            self.animator.play("happy", restart=True, next_anim="idle")
        else:
            self.animator.play("idle", restart=True)

    def _key_to_char(self, key: int) -> str | None:
        if pygame.K_a <= key <= pygame.K_z:
            return chr(key).upper()
        if pygame.K_0 <= key <= pygame.K_9:
            return chr(key)
        if key == pygame.K_SPACE and self.custom_name and not self.custom_name.endswith(" "):
            return " "
        return None

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            return ("title", {})

        if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_TAB):
            self.focus = "color" if self.focus == "name" else "name"
            return None

        if event.key == pygame.K_RETURN:
            pet = create_new_pet(self.custom_name, color=self.selected_color_id)
            return ("home", {"pet": pet, "offline": 0.0, "is_new": True})

        if self.focus == "color":
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.color_idx = (self.color_idx - 1) % len(PET_COLOR_ORDER)
                self._load_preview_animator(play_happy=True)
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE):
                self.color_idx = (self.color_idx + 1) % len(PET_COLOR_ORDER)
                self._load_preview_animator(play_happy=True)
            return None

        # Name field focused
        if event.key == pygame.K_BACKSPACE:
            self.custom_name = self.custom_name[:-1]
            return None

        ch = self._key_to_char(event.key)
        if ch and len(self.custom_name) < 10:
            self.custom_name += ch
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.animator.update(dt)

    def render(self, canvas: pygame.Surface) -> None:
        _draw_starfield(canvas, self.stars, self.elapsed)

        card = pygame.Rect(10, 6, 300, 136)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=6)

        header = self.fonts["sans"].render("HATCH A NEW PET", True, settings.COLOR_ACCENT)
        canvas.blit(header, ((settings.LOGICAL_WIDTH - header.get_width()) // 2, 10))
        pygame.draw.line(canvas, (72, 54, 108), (20, 26), (300, 26), 1)

        # Live recolored Sparkkit preview on the left
        pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(26, 102, 48, 8))
        canvas.blit(self.animator.get_frame(), (18, 44))

        # 7 mini color dots under the pet preview
        for i, cid in enumerate(PET_COLOR_ORDER):
            dx = 22 + i * 10
            swatch = PET_COLOR_PALETTES[cid]["swatch"]
            if i == self.color_idx:
                pygame.draw.rect(canvas, settings.COLOR_TEXT, (dx - 1, 114, 8, 8))
            pygame.draw.rect(canvas, swatch, (dx, 115, 6, 6))

        # --- Row 1: Name box (empty = default SPARKKIT) ---
        name_focused = self.focus == "name"
        lbl_name = self.fonts["sans"].render(
            "Name (blank = SPARKKIT):",
            True,
            settings.COLOR_TEXT if name_focused else settings.COLOR_MUTED,
        )
        canvas.blit(lbl_name, (96, 31))

        input_rect = pygame.Rect(96, 47, 202, 22)
        pygame.draw.rect(canvas, SEL_FILL if name_focused else settings.COLOR_BG, input_rect, border_radius=4)
        pygame.draw.rect(
            canvas,
            GOOD_COLOR if name_focused else settings.COLOR_ACCENT,
            input_rect,
            1,
            border_radius=4,
        )

        blink = "_" if (name_focused and int(self.elapsed * 2.5) % 2 == 0) else ""
        if self.custom_name:
            name_surf = self.fonts["mono"].render(self.custom_name + blink, True, settings.COLOR_TEXT)
        else:
            placeholder = f"SPARKKIT{blink}" if name_focused else "SPARKKIT (default)"
            name_surf = self.fonts["mono"].render(placeholder, True, settings.COLOR_MUTED)
        canvas.blit(name_surf, (103, 51))

        # --- Row 2: Base Color Picker ---
        color_focused = self.focus == "color"
        lbl_col = self.fonts["sans"].render(
            "Base Color:",
            True,
            settings.COLOR_TEXT if color_focused else settings.COLOR_MUTED,
        )
        canvas.blit(lbl_col, (96, 74))

        col_rect = pygame.Rect(96, 90, 202, 22)
        pygame.draw.rect(canvas, SEL_FILL if color_focused else settings.COLOR_BG, col_rect, border_radius=4)
        pygame.draw.rect(
            canvas,
            GOOD_COLOR if color_focused else settings.COLOR_ACCENT,
            col_rect,
            1,
            border_radius=4,
        )

        pal = PET_COLOR_PALETTES[self.selected_color_id]
        pygame.draw.rect(canvas, pal["swatch"], (103, 95, 12, 12), border_radius=2)
        pygame.draw.rect(canvas, settings.COLOR_TEXT, (103, 95, 12, 12), 1, border_radius=2)

        val_txt = f"< {pal['label']} >" if color_focused else pal["label"]
        val_surf = self.fonts["mono"].render(
            val_txt, True, GOOD_COLOR if color_focused else settings.COLOR_TEXT
        )
        canvas.blit(val_surf, (122, 94))

        # Overwrite notice / Hatch CTA
        if self.will_overwrite:
            warn = self.fonts["sans"].render("Replaces saved pet! [Enter] Hatch", True, WARN_COLOR)
            canvas.blit(warn, (96, 120))
        else:
            cta = self.fonts["sans"].render("[Enter] Hatch New Pet!", True, GOOD_COLOR)
            canvas.blit(cta, (96, 120))

        foot = (
            "Type Name  Up/Dn:Color  Enter:Hatch"
            if name_focused
            else "Lt/Rt:Color  Up/Dn:Name  Enter:Hatch"
        )
        _draw_footer(canvas, self.fonts["sans"], foot)


class SettingsScene:
    """Persistent user preferences saved to ~/.config/z-pet/config.json."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict):
        self.fonts = fonts
        self.config = config
        self.stars = _make_stars(20)
        self.elapsed = 0.0
        self.cursor = 0
        self.rows = ["clock", "sky", "speed", "back"]

    def _cycle_option(self, direction: int) -> None:
        key = self.rows[self.cursor]
        if key == "clock":
            self.config["clock_24h"] = not self.config.get("clock_24h", False)
        elif key == "sky":
            modes = [m[0] for m in SKY_OPTIONS]
            cur = self.config.get("sky_mode", "auto")
            idx = modes.index(cur) if cur in modes else 0
            self.config["sky_mode"] = modes[(idx + direction) % len(modes)]
        elif key == "speed":
            scales = [s[0] for s in SPEED_OPTIONS]
            cur = float(self.config.get("time_scale", 1.0))
            idx = scales.index(cur) if cur in scales else 0
            self.config["time_scale"] = scales[(idx + direction) % len(scales)]
        save_config(self.config)

    def _value_label(self, key: str) -> str:
        if key == "clock":
            return "24-Hour" if self.config.get("clock_24h") else "12-Hour"
        if key == "sky":
            cur = self.config.get("sky_mode", "auto")
            for mode_id, label in SKY_OPTIONS:
                if mode_id == cur:
                    return label
            return "Auto"
        if key == "speed":
            cur = float(self.config.get("time_scale", 1.0))
            for scale_val, label in SPEED_OPTIONS:
                if scale_val == cur:
                    return label
            return "1x Normal"
        return ""

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return ("title", {})
        if event.key in (pygame.K_UP, pygame.K_w):
            self.cursor = (self.cursor - 1) % len(self.rows)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.cursor = (self.cursor + 1) % len(self.rows)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            if self.rows[self.cursor] != "back":
                self._cycle_option(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            if self.rows[self.cursor] != "back":
                self._cycle_option(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.rows[self.cursor] == "back":
                return ("title", {})
            self._cycle_option(1)
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def render(self, canvas: pygame.Surface) -> None:
        _draw_starfield(canvas, self.stars, self.elapsed)

        card = pygame.Rect(14, 8, 292, 132)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=6)

        header = self.fonts["sans"].render("SETTINGS", True, settings.COLOR_ACCENT)
        canvas.blit(header, ((settings.LOGICAL_WIDTH - header.get_width()) // 2, 13))
        pygame.draw.line(canvas, (72, 54, 108), (24, 31), (296, 31), 1)

        labels = {
            "clock": "Clock Format",
            "sky": "Window Sky",
            "speed": "Game Speed",
            "back": "Save & Back",
        }

        for idx, key in enumerate(self.rows):
            row_y = 37 + idx * 24
            row_rect = pygame.Rect(22, row_y, 276, 22)
            is_selected = idx == self.cursor

            if is_selected:
                pygame.draw.rect(canvas, SEL_FILL, row_rect, border_radius=4)
                pygame.draw.rect(canvas, settings.COLOR_ACCENT, row_rect, 1, border_radius=4)

            text_col = settings.COLOR_TEXT if is_selected else settings.COLOR_MUTED
            if key == "back":
                lbl = self.fonts["sans"].render(
                    labels[key], True, GOOD_COLOR if is_selected else settings.COLOR_MUTED
                )
                canvas.blit(lbl, ((settings.LOGICAL_WIDTH - lbl.get_width()) // 2, row_y + 3))
            else:
                lbl = self.fonts["sans"].render(labels[key], True, text_col)
                canvas.blit(lbl, (30, row_y + 3))

                val_txt = f"< {self._value_label(key)} >" if is_selected else self._value_label(key)
                val_col = GOOD_COLOR if is_selected else settings.COLOR_ACCENT
                val_surf = self.fonts["mono"].render(val_txt, True, val_col)
                canvas.blit(val_surf, (290 - val_surf.get_width(), row_y + 3))

        _draw_footer(canvas, self.fonts["sans"], "Up/Dn:Row  Lt/Rt:Change  Esc:Back")