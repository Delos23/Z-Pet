"""Start-Up Title, New Pet (Starter + Base Color + Custom Name), and Settings scenes."""

import math
import random
import pygame
import hashlib
import settings

from core.animator import PET_COLOR_ORDER, PET_COLOR_PALETTES, load_species_animations
from core import sound
from core.species import get_personality, get_species, get_starter_ids
from core.save_manager import (
    create_new_pet,
    get_save_preview,
    has_save,
    load_pet,
    save_config,
)
from core.species import get_species, get_starter_ids
from core.display import KEYS_DOWN, KEYS_LEFT, KEYS_RIGHT, KEYS_UP

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
            ("guide", "The Guide"),
            ("settings", "Settings"),
            ("about", "About"),
            ("quit", "Quit"),
        ]
        self.cursor = 0 if self.save_exists else 1

        preview_species = self.preview["species_id"] if self.preview else "spark_kit"
        preview_color = self.preview["color"] if self.preview else "purple"
        sprite_dir = settings.SPRITES_DIR / preview_species
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

        if event.key in KEYS_UP:
          self.cursor = (self.cursor - 1) % len(self.items)
        elif event.key in KEYS_DOWN:
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
            if action == "guide":
             return ("guide", {"return_to": "title"})
            if action == "settings":
                return ("settings", {})
            if action == "about":
                return ("about", {"return_to": "title"})
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
            info_txt = f"{self.preview['name']} Lv.{self.preview['level']}"
            info_col = settings.COLOR_ACCENT if self.preview["alive"] else WARN_COLOR
        else:
            info_txt = "No pet saved yet"
            info_col = settings.COLOR_MUTED
        info_surf = self.fonts["sans"].render(info_txt, True, info_col)
        canvas.blit(info_surf, ((146 - info_surf.get_width()) // 2, 124))

        panel_rect = pygame.Rect(150, 8, 160, 134)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, panel_rect, border_radius=6)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, panel_rect, 1, border_radius=6)

        for idx, (action, label) in enumerate(self.items):
            row_y = 12 + idx * 21
            row_rect = pygame.Rect(158, row_y, 144, 19)
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
                canvas.blit(arrow, (164, row_y + (19 - arrow.get_height()) // 2))

            lbl_surf = self.fonts["sans"].render(display_lbl, True, text_col)
            canvas.blit(lbl_surf, (178, row_y + (19 - lbl_surf.get_height()) // 2))

        _draw_footer(canvas, self.fonts["sans"], "↑/↓:Move  Enter:Select  Esc:Quit")


class NewPetScene:
    """Hatch a new starter: pick Species, Base Color, and optional custom Name."""

    accepts_text_input = True

    def __init__(self, fonts: dict, config: dict):
        self.fonts = fonts
        self.config = config
        self.stars = _make_stars(20)
        self.elapsed = 0.0

        self.starter_ids = get_starter_ids()
        self.species_idx = 0
        self.color_idx = 0
        self.custom_name = ""
        self.rows = ["species", "color", "name"]
        self.focus_idx = 0
        self.will_overwrite = has_save()

        self._load_preview_animator(play_happy=True)

    @property
    def selected_species_id(self) -> str:
        return self.starter_ids[self.species_idx]

    @property
    def selected_color_id(self) -> str:
        return PET_COLOR_ORDER[self.color_idx]

    @property
    def focus(self) -> str:
        return self.rows[self.focus_idx]

    def _load_preview_animator(self, play_happy: bool = False) -> None:
        sprite_dir = settings.SPRITES_DIR / self.selected_species_id
        self.animator = load_species_animations(
            sprite_dir,
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

      if event.key == pygame.K_RETURN:
          pet = create_new_pet(
              self.custom_name,
              color=self.selected_color_id,
              species_id=self.selected_species_id,
          )
          return ("home", {"pet": pet, "offline": 0.0, "is_new": True})

      if self.focus == "name":
          if event.key == pygame.K_UP:
              self.focus_idx = (self.focus_idx - 1) % len(self.rows)
              return None
          if event.key in (pygame.K_DOWN, pygame.K_TAB):
              self.focus_idx = (self.focus_idx + 1) % len(self.rows)
              return None
          if event.key == pygame.K_BACKSPACE:
              self.custom_name = self.custom_name[:-1]
              return None
          ch = self._key_to_char(event.key)
          if ch and len(self.custom_name) < 10:
              self.custom_name += ch
          return None

        # Species & Color rows use F/X/Z/C and arrow keys
      if event.key in KEYS_UP:
          self.focus_idx = (self.focus_idx - 1) % len(self.rows)
          return None
      if event.key in KEYS_DOWN or event.key == pygame.K_TAB:
          self.focus_idx = (self.focus_idx + 1) % len(self.rows)
          return None

      if self.focus == "species":
          if event.key in KEYS_LEFT:
              self.species_idx = (self.species_idx - 1) % len(self.starter_ids)
              self._load_preview_animator(play_happy=True)
          elif event.key in KEYS_RIGHT or event.key == pygame.K_SPACE:
              self.species_idx = (self.species_idx + 1) % len(self.starter_ids)
              self._load_preview_animator(play_happy=True)
      elif self.focus == "color":
          if event.key in KEYS_LEFT:
              self.color_idx = (self.color_idx - 1) % len(PET_COLOR_ORDER)
              self._load_preview_animator(play_happy=True)
          elif event.key in KEYS_RIGHT or event.key == pygame.K_SPACE:
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
        sp = get_species(self.selected_species_id)
        pers = get_personality(self.selected_species_id)

        card = pygame.Rect(8, 6, 304, 138)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=6)

        header = self.fonts["sans"].render("HATCH A NEW PET", True, settings.COLOR_ACCENT)
        canvas.blit(header, ((settings.LOGICAL_WIDTH - header.get_width()) // 2, 9))
        pygame.draw.line(canvas, (72, 54, 108), (18, 25), (302, 25), 1)

        # Left preview stage: live species + color sprite, 7 color dots, personality badge
        pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(24, 94, 48, 8))
        canvas.blit(self.animator.get_frame(), (16, 36))

        for i, cid in enumerate(PET_COLOR_ORDER):
            dx = 18 + i * 10
            swatch = PET_COLOR_PALETTES[cid]["swatch"]
            if i == self.color_idx:
                pygame.draw.rect(canvas, settings.COLOR_TEXT, (dx - 1, 105, 8, 8))
            pygame.draw.rect(canvas, swatch, (dx, 106, 6, 6))

        trait_s = self.fonts["sans"].render(pers["label"], True, WARN_COLOR)
        canvas.blit(trait_s, (max(12, (94 - trait_s.get_width()) // 2), 119))

        # --- Row 0: Starter Species ---
        sp_focused = self.focus == "species"
        r0 = pygame.Rect(98, 28, 206, 22)
        pygame.draw.rect(canvas, SEL_FILL if sp_focused else settings.COLOR_BG, r0, border_radius=4)
        pygame.draw.rect(canvas, GOOD_COLOR if sp_focused else settings.COLOR_ACCENT, r0, 1, border_radius=4)
        canvas.blit(
            self.fonts["sans"].render("Pet:", True, settings.COLOR_TEXT if sp_focused else settings.COLOR_MUTED),
            (104, 31),
        )
        sp_val = f"< {sp['name']} >" if sp_focused else sp["name"]
        sp_surf = self.fonts["mono"].render(sp_val, True, GOOD_COLOR if sp_focused else settings.COLOR_TEXT)
        canvas.blit(sp_surf, (298 - sp_surf.get_width(), 31))

        # --- Row 1: Base Color ---
        col_focused = self.focus == "color"
        pal = PET_COLOR_PALETTES[self.selected_color_id]
        r1 = pygame.Rect(98, 53, 206, 22)
        pygame.draw.rect(canvas, SEL_FILL if col_focused else settings.COLOR_BG, r1, border_radius=4)
        pygame.draw.rect(canvas, GOOD_COLOR if col_focused else settings.COLOR_ACCENT, r1, 1, border_radius=4)
        pygame.draw.rect(canvas, pal["swatch"], (104, 58, 12, 12), border_radius=2)
        pygame.draw.rect(canvas, settings.COLOR_TEXT, (104, 58, 12, 12), 1, border_radius=2)
        canvas.blit(
            self.fonts["sans"].render("Color:", True, settings.COLOR_TEXT if col_focused else settings.COLOR_MUTED),
            (120, 56),
        )
        col_val = f"< {pal['label']} >" if col_focused else pal["label"]
        col_surf = self.fonts["mono"].render(col_val, True, GOOD_COLOR if col_focused else settings.COLOR_TEXT)
        canvas.blit(col_surf, (298 - col_surf.get_width(), 56))

        # --- Row 2: Custom Name ---
        name_focused = self.focus == "name"
        r2 = pygame.Rect(98, 78, 206, 22)
        pygame.draw.rect(canvas, SEL_FILL if name_focused else settings.COLOR_BG, r2, border_radius=4)
        pygame.draw.rect(canvas, GOOD_COLOR if name_focused else settings.COLOR_ACCENT, r2, 1, border_radius=4)
        canvas.blit(
            self.fonts["sans"].render("Name:", True, settings.COLOR_TEXT if name_focused else settings.COLOR_MUTED),
            (104, 81),
        )
        blink = "_" if (name_focused and int(self.elapsed * 2.5) % 2 == 0) else ""
        if self.custom_name:
            name_surf = self.fonts["mono"].render(self.custom_name + blink, True, settings.COLOR_TEXT)
        else:
            name_surf = self.fonts["mono"].render(f"{sp['default_name']}{blink}", True, settings.COLOR_MUTED)
        canvas.blit(name_surf, (150, 81))

        # --- Row 3: Starter Ability ---
        ab_name = sp["ability"]["name"] if sp.get("ability") else "None"
        ab_s = self.fonts["sans"].render(f"Skill: {ab_name}", True, settings.COLOR_ACCENT)
        canvas.blit(ab_s, (98, 104))

        # --- Row 4: Starting Stats (or overwrite warning) ---
        st = sp["base_stats"]
        if self.will_overwrite:
            notice = self.fonts["mono"].render(
                f"A:{st['atk']} D:{st['def']} S:{st['spd']} I:{st['int']} (New!)",
                True,
                WARN_COLOR,
            )
        else:
            notice = self.fonts["mono"].render(
                f"A:{st['atk']} D:{st['def']} S:{st['spd']} I:{st['int']} [Enter]",
                True,
                GOOD_COLOR,
            )
        canvas.blit(notice, (98, 121))

        foot = (
          "Type Name  Bksp:Del  ↑/↓:Row  Enter:Hatch"
          if name_focused
          else "←/→:Pick  ↑/↓:Row  Enter:Hatch"
       )
        _draw_footer(canvas, self.fonts["sans"], foot)


import hashlib

# SHA-256 hash of your private 4-12 digit code (digits 1-9) to reveal Game Speed
DEV_SPEED_HASH = "a6e0f1a76758711ecc0404d508d188f3d05e40247fda62936f10624934d34d43"


class SettingsScene:
    """User preferences: SFX/Music volume levels, 12h/24h Clock, and Window Sky."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict):
        self.fonts = fonts
        self.config = config
        self.dev_unlocked = float(self.config.get("time_scale", 1.0)) != 1.0
        self.rows = ["sfx", "music", "clock_24h", "sky_mode", "back"]
        if self.dev_unlocked:
            self.rows.insert(self.rows.index("back"), "time_scale")
        self.cursor = 0
        self._code_buf = ""

    def _try_unlock_dev_speed(self, event: pygame.event.Event) -> bool:
        """Unlocks the hidden Game Speed row when the private digit code is entered."""
        if self.dev_unlocked or not DEV_SPEED_HASH:
            return False

        digit = ""
        key = getattr(event, "key", None)
        uni = getattr(event, "unicode", "")
        if isinstance(key, int) and pygame.K_1 <= key <= pygame.K_9:
            digit = chr(ord("1") + (key - pygame.K_1))
        elif isinstance(uni, str) and len(uni) == 1 and uni in "123456789":
            digit = uni

        if not digit:
            return False

        self._code_buf = (self._code_buf + digit)[-12:]
        for length in range(4, len(self._code_buf) + 1):
            candidate = self._code_buf[-length:]
            if hashlib.sha256(candidate.encode("utf-8")).hexdigest() == DEV_SPEED_HASH:
                self.dev_unlocked = True
                self._code_buf = ""
                if "time_scale" not in self.rows:
                    self.rows.insert(self.rows.index("back"), "time_scale")
                self.cursor = self.rows.index("time_scale")
                sound.play("evolve")
                return True
        return True

    def _cycle_option(self, delta: int) -> None:
        key = self.rows[self.cursor]
        if key == "sfx":
            levels = sound.VOLUME_LEVELS
            cur = sound.normalize_volume(self.config.get("sfx", "high"))
            new_lvl = levels[(levels.index(cur) + delta) % len(levels)]
            self.config["sfx"] = new_lvl
            sound.set_sfx_level(new_lvl)
            if new_lvl != "off":
                sound.play("select")
        elif key == "music":
            levels = sound.VOLUME_LEVELS
            cur = sound.normalize_volume(self.config.get("music", "high"))
            new_lvl = levels[(levels.index(cur) + delta) % len(levels)]
            self.config["music"] = new_lvl
            sound.set_music_level(new_lvl)
            sound.play("click")
        elif key == "clock_24h":
            self.config["clock_24h"] = not self.config.get("clock_24h", False)
            sound.play("click")
        elif key == "sky_mode":
            modes = ["auto", "dawn", "day", "sunset", "night"]
            cur = self.config.get("sky_mode", "auto")
            idx = modes.index(cur) if cur in modes else 0
            self.config["sky_mode"] = modes[(idx + delta) % len(modes)]
            sound.play("click")
            sound.set_mood("somber" if sound.is_night_time(self.config) else "day")
        elif key == "time_scale" and self.dev_unlocked:
            scales = [1.0, 10.0, 60.0]
            cur = float(self.config.get("time_scale", 1.0))
            idx = scales.index(cur) if cur in scales else 0
            self.config["time_scale"] = scales[(idx + delta) % len(scales)]
            sound.play("click")

        # Always persist 1x Normal to disk so dev speed is strictly session-only
        persisted = dict(self.config)
        persisted["time_scale"] = 1.0
        save_config(persisted)

    def _value_label(self, key: str) -> str:
        if key in ("sfx", "music"):
            return sound.normalize_volume(self.config.get(key, "high")).upper()
        if key == "clock_24h":
            return "24-Hour" if self.config.get("clock_24h", False) else "12-Hour"
        if key == "sky_mode":
            return str(self.config.get("sky_mode", "auto")).title()
        if key == "time_scale":
            s = float(self.config.get("time_scale", 1.0))
            return "1x Normal" if s == 1.0 else (f"{int(s)}x Fast" if s == 10.0 else f"{int(s)}x Test")
        return ""

    def _value_color(self, key: str) -> tuple[int, int, int]:
        if key in ("sfx", "music"):
            lvl = sound.normalize_volume(self.config.get(key, "high"))
            return {
                "off": (240, 95, 115),
                "low": (126, 206, 255),
                "med": (255, 224, 96),
                "high": (105, 225, 145),
            }[lvl]
        return (255, 224, 96)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None
        if self._try_unlock_dev_speed(event):
            return None
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            sound.play("back")
            return ("title", {})
        if event.key in KEYS_UP:
            self.cursor = (self.cursor - 1) % len(self.rows)
            sound.play("click")
        elif event.key in KEYS_DOWN:
            self.cursor = (self.cursor + 1) % len(self.rows)
            sound.play("click")
        elif event.key in KEYS_LEFT:
            if self.rows[self.cursor] != "back":
                self._cycle_option(-1)
        elif event.key in KEYS_RIGHT:
            if self.rows[self.cursor] != "back":
                self._cycle_option(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.rows[self.cursor] == "back":
                sound.play("back")
                return ("title", {})
            self._cycle_option(1)
        return None

    def update(self, dt: float) -> None:
        return None

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill(settings.COLOR_BG)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 24), (settings.LOGICAL_WIDTH, 24), 1)
        title_s = self.fonts["sans"].render("SETTINGS", True, (255, 224, 96))
        canvas.blit(title_s, (10, 4))

        labels = {
            "sfx": "Sound FX",
            "music": "Music",
            "clock_24h": "Clock Format",
            "sky_mode": "Window Sky",
            "time_scale": "Game Speed",
            "back": "Back to Menu",
        }

        for idx, key in enumerate(self.rows):
            ry = 29 + idx * 19
            rect = pygame.Rect(14, ry, 292, 17)
            selected = idx == self.cursor
            pygame.draw.rect(canvas, (76, 52, 122) if selected else settings.COLOR_PANEL, rect, border_radius=4)
            pygame.draw.rect(
                canvas,
                (105, 225, 145) if selected else settings.COLOR_ACCENT,
                rect,
                1,
                border_radius=4,
            )

            lbl_s = self.fonts["sans"].render(
                labels[key], True, settings.COLOR_TEXT if selected else settings.COLOR_MUTED
            )
            canvas.blit(lbl_s, (24, ry + (17 - lbl_s.get_height()) // 2))

            if key != "back":
                val_txt = f"< {self._value_label(key)} >"
                val_col = self._value_color(key) if selected else settings.COLOR_MUTED
                val_s = self.fonts["mono"].render(val_txt, True, val_col)
                canvas.blit(val_s, (rect.right - val_s.get_width() - 10, ry + (17 - val_s.get_height()) // 2))

        _draw_footer(canvas, self.fonts["sans"], "↑/↓:Row  ←/→:Change  Esc:Back")