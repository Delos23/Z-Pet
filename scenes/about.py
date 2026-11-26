"""About screen for Z-Pet (Credits, Controls, and System info)."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import pygame

import settings
from core import sound


def _load_app_meta() -> dict[str, str]:
    """Reads version and author metadata from app-builder.json with safe fallbacks."""
    meta = {
        "app_name": "Z-Pet",
        "version": "1.0.0",
        "author": "Aaron Bumbarger",
        "github": "delos23",
        "license": "MIT",
        "repo": "github.com/delos23/z-pet",
    }
    manifest = settings.BASE_DIR / "app-builder.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        store = data.get("store", {})
        author = store.get("author", {})
        meta["app_name"] = str(data.get("app_name", meta["app_name"]))
        meta["version"] = str(data.get("version", meta["version"]))
        meta["author"] = str(author.get("display_name", meta["author"]))
        meta["github"] = str(author.get("github", meta["github"]))
        meta["license"] = str(store.get("license", meta["license"]))
        repo = str(store.get("source_repo", meta["repo"]))
        meta["repo"] = repo.replace("https://", "").replace("http://", "")
    except (OSError, ValueError, TypeError):
        pass
    return meta


def _short_path(path: Path, max_len: int = 28) -> str:
    """Formats a path with ~ for home and trims cleanly if too long for 320px."""
    try:
        rel = path.resolve().relative_to(Path.home().resolve())
        text = f"~/{rel.as_posix()}"
    except ValueError:
        text = path.as_posix()
    if len(text) <= max_len:
        return text
    return "..." + text[-(max_len - 3) :]


def _audio_status() -> str:
    init = pygame.mixer.get_init()
    if not init:
        return "Inactive / Silent"
    freq, _, channels = init
    ch_label = "Mono" if channels == 1 else f"{channels}ch"
    return f"{freq // 1000} kHz {ch_label}"


class AboutScene:
    """3-tab About screen: Credits, Controls, and System diagnostics."""

    TABS = ("Credits", "Controls", "System")
    accepts_text_input = False

    def __init__(
        self,
        fonts: dict[str, pygame.font.Font],
        config: dict | None = None,
        return_to: str = "title",
        return_payload: dict | None = None,
    ) -> None:
        self.fonts = fonts
        self.config = config or {}
        self.return_to = return_to
        self.return_payload = return_payload or {}
        self.tab_idx = 0
        self.meta = _load_app_meta()

        self.font_sans = fonts.get("sans") or next(iter(fonts.values()))
        self.font_mono = fonts.get("mono") or self.font_sans
        self.font_title = fonts.get("title") or fonts.get("bold") or self.font_sans

        self.col_bg = getattr(settings, "COLOR_BG", (24, 18, 38))
        self.col_panel = getattr(settings, "COLOR_PANEL", (36, 26, 56))
        self.col_border = getattr(settings, "COLOR_BORDER", (88, 66, 128))
        self.col_text = getattr(settings, "COLOR_TEXT", (242, 238, 250))
        self.col_muted = getattr(settings, "COLOR_MUTED", (166, 156, 194))
        self.col_accent = getattr(settings, "COLOR_ACCENT", (186, 132, 255))
        self.col_gold = (255, 214, 92)

    def _rows_for_tab(self) -> list[tuple[str, str]]:
        if self.tab_idx == 0:
            return [
                ("Creator", f"{self.meta['author']} ({self.meta['github']})"),
                ("Created", "November 2026"),
                ("Version", f"v{self.meta['version']}  ({self.meta['license']} License)"),
                ("Target", "M5Stack Cardputer Zero"),
                ("Roster", "5 Starters  /  35 Evolutions"),
                ("GitHub", self.meta["repo"]),
            ]
        if self.tab_idx == 1:
            return [
                ("Move", "Arrows or F / X / Z / C"),
                ("Action", "Enter / Space    Back: Esc / Q"),
                ("Guide", "Press G on Status screen"),
                ("Volume", "fn+D Up / fn+S Dn / fn+A Mute"),
                ("Shot", "0 (Cardputer) or F12 (PC)"),
                ("Care", "48h unattended grace timer"),
            ]
        return [
            ("Display", f"{settings.LOGICAL_WIDTH}x{settings.LOGICAL_HEIGHT} Pixel Canvas"),
            ("Audio", _audio_status()),
            ("Runtime", f"Python {sys.version_info.major}.{sys.version_info.minor} / Pygame"),
            ("OS", f"{platform.system()} ({platform.machine()})"),
            ("App Dir", _short_path(settings.BASE_DIR)),
            ("Saves", _short_path(settings.SAVE_DIR)),
        ]

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_q, pygame.K_BACKSPACE):
            sound.play("back")
            return (self.return_to, self.return_payload)

        if event.key in (pygame.K_LEFT, pygame.K_z):
            self.tab_idx = (self.tab_idx - 1) % len(self.TABS)
            sound.play("click")
        elif event.key in (pygame.K_RIGHT, pygame.K_c, pygame.K_TAB):
            self.tab_idx = (self.tab_idx + 1) % len(self.TABS)
            sound.play("click")
        elif event.key == pygame.K_1:
            self.tab_idx = 0
            sound.play("click")
        elif event.key == pygame.K_2:
            self.tab_idx = 1
            sound.play("click")
        elif event.key == pygame.K_3:
            self.tab_idx = 2
            sound.play("click")

        return None

    def update(self, dt: float) -> tuple[str, dict] | None:
        return None

    def _draw_arrow(self, canvas: pygame.Surface, x: int, y: int, direction: int, color: tuple[int, int, int]) -> None:
        """Draws a crisp 4x7 pixel arrow icon (-1 left, +1 right)."""
        if direction < 0:
            pts = ((x + 3, y), (x, y + 3), (x + 3, y + 6))
        else:
            pts = ((x, y), (x + 3, y + 3), (x, y + 6))
        pygame.draw.polygon(canvas, color, pts)

    def draw(self, canvas: pygame.Surface) -> None:
        w, h = settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT
        canvas.fill(self.col_bg)

        # Header bar
        pygame.draw.rect(canvas, (30, 22, 48), (0, 0, w, 22))
        pygame.draw.line(canvas, self.col_border, (0, 22), (w, 22))

        title = self.font_title.render(f"ABOUT {self.meta['app_name'].upper()}", True, self.col_gold)
        ver = self.font_mono.render(f"v{self.meta['version']}", True, self.col_accent)
        canvas.blit(title, (10, (22 - title.get_height()) // 2))
        canvas.blit(ver, (w - ver.get_width() - 10, (22 - ver.get_height()) // 2))

        # Compact tab bar
        tab_y, tab_h = 26, 16
        tab_w = 88
        gap = 8
        total_w = len(self.TABS) * tab_w + (len(self.TABS) - 1) * gap
        start_x = (w - total_w) // 2

        self._draw_arrow(canvas, start_x - 11, tab_y + 4, -1, self.col_muted)
        self._draw_arrow(canvas, start_x + total_w + 7, tab_y + 4, 1, self.col_muted)

        for idx, label in enumerate(self.TABS):
            tx = start_x + idx * (tab_w + gap)
            active = idx == self.tab_idx
            fill = self.col_accent if active else self.col_panel
            border = self.col_gold if active else self.col_border
            txt_col = (22, 16, 34) if active else self.col_muted
            pygame.draw.rect(canvas, fill, (tx, tab_y, tab_w, tab_h), border_radius=3)
            pygame.draw.rect(canvas, border, (tx, tab_y, tab_w, tab_h), 1, border_radius=3)
            surf = self.font_sans.render(label, True, txt_col)
            canvas.blit(surf, (tx + (tab_w - surf.get_width()) // 2, tab_y + (tab_h - surf.get_height()) // 2))

        # Main info card
        card = pygame.Rect(8, 46, w - 16, 102)
        pygame.draw.rect(canvas, self.col_panel, card, border_radius=4)
        pygame.draw.rect(canvas, self.col_border, card, 1, border_radius=4)

        rows = self._rows_for_tab()
        row_y = card.y + 6
        row_step = 15
        for label, value in rows:
            lbl_surf = self.font_mono.render(f"{label}:", True, self.col_accent)
            val_surf = self.font_sans.render(value, True, self.col_text)
            canvas.blit(lbl_surf, (card.x + 8, row_y))
            canvas.blit(val_surf, (card.x + 76, row_y))
            row_y += row_step

        # Footer hint
        footer = self.font_sans.render("Arrows: Switch Tab    Esc: Back", True, self.col_muted)
        canvas.blit(footer, ((w - footer.get_width()) // 2, h - footer.get_height() - 5))