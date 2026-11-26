"""The Guide: 35-species discovery tracker, Personality traits, and Care evolution guide."""

import pygame

import settings
from core.animator import recolor_surface
from core.display import KEYS_DOWN, KEYS_LEFT, KEYS_RIGHT, KEYS_UP
from core.save_manager import get_save_preview, load_discovered_species, record_discovery
from core import sound
from core.species import (
    ADULT_EVOLVE_LEVEL,
    CARE_PATH_META,
    TEEN_EVOLVE_LEVEL,
    get_personality,
    get_species,
    get_starter_ids,
    load_species_db,
)

SEL_FILL = (76, 52, 122)
TAB_ACTIVE = (94, 66, 152)
GOOD_COL = (105, 225, 145)
GOLD_COL = (255, 224, 96)
CYAN_COL = (126, 206, 255)
WARN_COL = (245, 165, 95)
LOCK_SILHOUETTE = (40, 28, 66, 255)

TABS = ["SPECIES", "TRAITS", "CARE"]

TRAIT_DETAILS = [
    (
        "hyper",
        "Hyper",
        "Sparkkit",
        ["+25% Star Catch XP", "+25% faster room walk"],
        "Hunger drains 15% faster",
    ),
    (
        "bold",
        "Bold",
        "Cinderpup",
        ["+25% Teach drill XP", "Meals give +4 Hunger"],
        "Energy drains 10% faster",
    ),
    (
        "serene",
        "Serene",
        "Aquafin",
        ["Energy drains 20% slower", "+20% faster sleep rest"],
        "Clean drains 10% faster",
    ),
    (
        "gentle",
        "Gentle",
        "Sproutowl",
        ["+1 Bond on Hug & Treat", "Hunger drains 20% slower"],
        "Calm, slower room walk",
    ),
    (
        "curious",
        "Curious",
        "Cogbit",
        ["+25% Feed/Hug/Clean XP", "+1 stat on Perfect drill"],
        "Happy drains 15% faster",
    ),
]

CARE_TOPICS = [
    (
        "Radiant",
        GOOD_COL,
        "Attentive, high-Bond care",
        [
            f"Lv.{TEEN_EVOLVE_LEVEL}: 0-1 MST, BND 20+",
            f"Lv.{ADULT_EVOLVE_LEVEL}: 0-2 MST, BND 45+",
            "Feed, hug, clean & play",
            "Balanced & mystic forms",
        ],
    ),
    (
        "Trained",
        CYAN_COL,
        "Focused on Teach Drills",
        [
            f"Lv.{TEEN_EVOLVE_LEVEL}: 4+ Drills, <=2 MST",
            f"Lv.{ADULT_EVOLVE_LEVEL}: 9+ Drills, <=3 MST",
            "Hit daily Teach drills",
            "Combat & armored forms",
        ],
    ),
    (
        "Wild",
        WARN_COL,
        "Scrappy rogue evolution",
        [
            f"Lv.{TEEN_EVOLVE_LEVEL}: 3+ MST or low BND",
            f"Lv.{ADULT_EVOLVE_LEVEL}: 5+ MST or low BND",
            "Fierce high-ATK forms!",
            "Teens can switch paths",
        ],
    ),
    (
        "Mistakes",
        (240, 110, 125),
        "How Care Mistakes happen",
        [
            "HG, HP, or CL below 15%",
            "Or 3+ poops on the floor",
            "30+ min ignored = +1 MST",
            "Care quickly to reset",
        ],
    ),
]


def _wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    """Splits text into lines that fit cleanly within max_w pixels."""
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if font.size(trial)[0] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _build_catalog() -> tuple[list[str], dict[str, dict]]:
    """Orders all 35 species by starter family and computes evolution unlock hints."""
    db = load_species_db()
    ordered: list[str] = []
    meta: dict[str, dict] = {}

    for starter_id in get_starter_ids():
        starter = db[starter_id]
        starter_name = starter["name"]

        ordered.append(starter_id)
        meta[starter_id] = {
            "family": starter_name,
            "path": None,
            "hint": "Starter - Pick in New Pet",
            "next_hint": f"Evolves to Teen at Lv.{TEEN_EVOLVE_LEVEL}",
        }

        teens = starter.get("evolutions", {})
        adult_added: set[str] = set()
        adult_order: list[tuple[str, str]] = []

        for path_key in ("radiant", "trained", "wild"):
            teen_id = teens.get(path_key)
            if not teen_id or teen_id not in db:
                continue
            path_lbl = CARE_PATH_META[path_key][0]
            ordered.append(teen_id)
            meta[teen_id] = {
                "family": starter_name,
                "path": path_key,
                "hint": f"{starter_name} Lv.{TEEN_EVOLVE_LEVEL} ({path_lbl})",
                "next_hint": f"Evolves to Adult at Lv.{ADULT_EVOLVE_LEVEL}",
            }

            adults = db[teen_id].get("evolutions", {})
            for a_path in ("radiant", "trained", "wild"):
                adult_id = adults.get(a_path)
                if adult_id and adult_id in db and adult_id not in adult_added:
                    adult_added.add(adult_id)
                    adult_order.append((a_path, adult_id))

        for a_path, adult_id in adult_order:
            a_lbl = CARE_PATH_META[a_path][0]
            ordered.append(adult_id)
            meta[adult_id] = {
                "family": starter_name,
                "path": a_path,
                "hint": f"{starter_name} Lv.{ADULT_EVOLVE_LEVEL} ({a_lbl})",
                "next_hint": "Final Adult Form",
            }

    return ordered, meta


class GuideScene:
    """In-game encyclopedia: Species discoveries, Personality traits, and Care rules."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict, return_to: str = "title", pet=None):
        self.fonts = fonts
        self.config = config
        self.return_to = return_to
        self.pet = pet

        # Ensure any currently saved pet is recorded in The Guide immediately
        if pet is not None:
            record_discovery(pet.species_id)
        else:
            preview = get_save_preview()
            if preview:
                record_discovery(preview["species_id"])

        self.discovered = load_discovered_species()
        self.catalog, self.lineage = _build_catalog()

        self.tab_idx = 0
        self.species_idx = 0
        self.trait_idx = 0
        self.care_idx = 0

        # Jump straight to the active pet if opened from Status
        if pet is not None and pet.species_id in self.catalog:
            self.species_idx = self.catalog.index(pet.species_id)

        self._sprite_cache: dict[tuple[str, bool], pygame.Surface] = {}

    def _get_preview_sprite(self, species_id: str, unlocked: bool) -> pygame.Surface:
        key = (species_id, unlocked)
        if key in self._sprite_cache:
            return self._sprite_cache[key]

        size = settings.SPRITE_SIZE * settings.SPRITE_SCALE
        path = settings.SPRITES_DIR / species_id / "idle.png"
        if path.exists():
            sheet = pygame.image.load(str(path)).convert_alpha()
            frame = sheet.subsurface(pygame.Rect(0, 0, settings.SPRITE_SIZE, settings.SPRITE_SIZE)).copy()
            if unlocked and self.pet is not None and self.pet.species_id == species_id:
                frame = recolor_surface(frame, self.pet.color)
            scaled = pygame.transform.scale(frame, (size, size))
        else:
            scaled = pygame.Surface((size, size), pygame.SRCALPHA)

        if not unlocked:
            mask = pygame.mask.from_surface(scaled)
            scaled = mask.to_surface(setcolor=LOCK_SILHOUETTE, unsetcolor=(0, 0, 0, 0))

        self._sprite_cache[key] = scaled
        return scaled

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            sound.play("back")
            if self.return_to == "status" and self.pet is not None:
                return ("status", {"pet": self.pet})
            return ("title", {})

        if event.key in KEYS_LEFT:
            self.tab_idx = (self.tab_idx - 1) % len(TABS)
            sound.play("click")
        elif event.key in KEYS_RIGHT or event.key == pygame.K_TAB:
            self.tab_idx = (self.tab_idx + 1) % len(TABS)
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
        elif event.key in KEYS_UP:
            if self.tab_idx == 0:
                self.species_idx = (self.species_idx - 1) % len(self.catalog)
            elif self.tab_idx == 1:
                self.trait_idx = (self.trait_idx - 1) % len(TRAIT_DETAILS)
            else:
                self.care_idx = (self.care_idx - 1) % len(CARE_TOPICS)
            sound.play("click")
        elif event.key in KEYS_DOWN:
            if self.tab_idx == 0:
                self.species_idx = (self.species_idx + 1) % len(self.catalog)
            elif self.tab_idx == 1:
                self.trait_idx = (self.trait_idx + 1) % len(TRAIT_DETAILS)
            else:
                self.care_idx = (self.care_idx + 1) % len(CARE_TOPICS)
            sound.play("click")
        return None

    def update(self, dt: float) -> None:
        return None

    def _draw_top_tabs(self, canvas: pygame.Surface) -> None:
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 24), (settings.LOGICAL_WIDTH, 24), 1)

        title_s = self.fonts["sans"].render("THE GUIDE", True, GOLD_COL)
        canvas.blit(title_s, (8, 4))

        tab_x = 96
        for idx, name in enumerate(TABS):
            w = 72
            rect = pygame.Rect(tab_x + idx * (w + 2), 3, w, 18)
            active = idx == self.tab_idx
            pygame.draw.rect(canvas, TAB_ACTIVE if active else settings.COLOR_BG, rect, border_radius=3)
            pygame.draw.rect(
                canvas,
                GOOD_COL if active else settings.COLOR_ACCENT,
                rect,
                1,
                border_radius=3,
            )
            lbl = self.fonts["mono"].render(name, True, settings.COLOR_TEXT if active else settings.COLOR_MUTED)
            canvas.blit(lbl, (rect.x + (w - lbl.get_width()) // 2, rect.y + 2))

    def _draw_species_tab(self, canvas: pygame.Surface) -> None:
        sid = self.catalog[self.species_idx]
        sp = get_species(sid)
        lin = self.lineage[sid]
        unlocked = sid in self.discovered

        # Left portrait card
        left = pygame.Rect(6, 28, 98, 116)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, left, border_radius=5)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, left, 1, border_radius=5)

        num_s = self.fonts["mono"].render(
            f"#{self.species_idx + 1:02d}/{len(self.catalog)}", True, settings.COLOR_MUTED
        )
        canvas.blit(num_s, (left.x + (left.w - num_s.get_width()) // 2, 31))

        sprite = self._get_preview_sprite(sid, unlocked)
        pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(31, 98, 48, 8))
        canvas.blit(sprite, (23, 40))

        if not unlocked:
            q_s = self.fonts["title"].render("?", True, settings.COLOR_ACCENT)
            canvas.blit(q_s, (left.x + (left.w - q_s.get_width()) // 2, 60))

        stage_s = self.fonts["mono"].render(sp["stage"].upper(), True, GOLD_COL if unlocked else settings.COLOR_MUTED)
        canvas.blit(stage_s, (left.x + (left.w - stage_s.get_width()) // 2, 108))

        found_s = self.fonts["sans"].render(
            f"Found: {len(self.discovered)}/{len(self.catalog)}", True, GOOD_COL
        )
        canvas.blit(found_s, (left.x + (left.w - found_s.get_width()) // 2, 124))

        # Right details card
        right = pygame.Rect(108, 28, 206, 116)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, right, border_radius=5)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, right, 1, border_radius=5)

        canvas.set_clip(right.inflate(-4, -4))
        max_w = right.w - 14

        if unlocked:
            pers = get_personality(sid)
            name_s = self.fonts["sans"].render(sp["name"], True, settings.COLOR_TEXT)
            canvas.blit(name_s, (115, 32))

            trait_s = self.fonts["mono"].render(pers["label"], True, WARN_COL)
            canvas.blit(trait_s, (right.right - trait_s.get_width() - 7, 32))

            tag_s = self.fonts["sans"].render(sp["tagline"], True, settings.COLOR_MUTED)
            canvas.blit(tag_s, (115, 47))

            st = sp["base_stats"]
            stat_s = self.fonts["mono"].render(
                f"A:{st['atk']:02d} D:{st['def']:02d} S:{st['spd']:02d} I:{st['int']:02d}",
                True,
                CYAN_COL,
            )
            canvas.blit(stat_s, (115, 63))

            pygame.draw.line(canvas, (72, 54, 108), (115, 79), (right.right - 7, 79), 1)

            ab = sp.get("ability") or {}
            ab_name = ab.get("name", "None")
            ab_desc = ab.get("desc", "")
            canvas.blit(self.fonts["sans"].render(f"Skill: {ab_name}", True, GOLD_COL), (115, 82))
            for i, line in enumerate(_wrap_text(self.fonts["sans"], ab_desc, max_w)[:2]):
                canvas.blit(self.fonts["sans"].render(line, True, settings.COLOR_MUTED), (115, 97 + i * 13))

            path_key = lin.get("path")
            hint_col = CARE_PATH_META[path_key][1] if path_key in CARE_PATH_META else GOOD_COL
            hint_txt = lin["hint"] if sp["stage"] != "baby" else lin["next_hint"]
            canvas.blit(self.fonts["sans"].render(hint_txt, True, hint_col), (115, 126))
        else:
            canvas.blit(self.fonts["sans"].render("??? (Undiscovered)", True, settings.COLOR_MUTED), (115, 33))
            fam_s = self.fonts["sans"].render(f"Family: {lin['family']}", True, settings.COLOR_ACCENT)
            canvas.blit(fam_s, (115, 51))

            pygame.draw.line(canvas, (72, 54, 108), (115, 69), (right.right - 7, 69), 1)

            canvas.blit(self.fonts["sans"].render("How to unlock:", True, GOLD_COL), (115, 74))
            for i, line in enumerate(_wrap_text(self.fonts["sans"], lin["hint"], max_w)[:2]):
                canvas.blit(self.fonts["sans"].render(line, True, settings.COLOR_TEXT), (115, 91 + i * 15))

            canvas.blit(self.fonts["mono"].render("A:?? D:?? S:?? I:??", True, settings.COLOR_MUTED), (115, 124))

        canvas.set_clip(None)

    def _draw_traits_tab(self, canvas: pygame.Surface) -> None:
        # Left trait selector (compact 82px column leaves 222px for details)
        for idx, (_pid, label, _line, _perks, _trade) in enumerate(TRAIT_DETAILS):
            ry = 29 + idx * 23
            rect = pygame.Rect(6, ry, 82, 20)
            selected = idx == self.trait_idx
            pygame.draw.rect(canvas, SEL_FILL if selected else settings.COLOR_PANEL, rect, border_radius=4)
            pygame.draw.rect(canvas, GOOD_COL if selected else settings.COLOR_ACCENT, rect, 1, border_radius=4)
            lbl = self.fonts["sans"].render(
                label, True, settings.COLOR_TEXT if selected else settings.COLOR_MUTED
            )
            canvas.blit(lbl, (12, ry + 2))

        # Right trait detail card
        _pid, label, line_name, perks, tradeoff = TRAIT_DETAILS[self.trait_idx]
        card = pygame.Rect(92, 28, 222, 116)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=5)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=5)

        canvas.set_clip(card.inflate(-4, -4))
        text_x = card.x + 8
        max_w = card.w - 16

        canvas.blit(self.fonts["sans"].render(f"{label} Trait", True, GOLD_COL), (text_x, 33))
        line_s = self.fonts["mono"].render(line_name, True, settings.COLOR_ACCENT)
        canvas.blit(line_s, (card.right - line_s.get_width() - 8, 33))
        pygame.draw.line(canvas, (72, 54, 108), (text_x, 49), (card.right - 8, 49), 1)

        y = 53
        canvas.blit(self.fonts["sans"].render("Perks:", True, GOOD_COL), (text_x, y))
        y += 14
        for perk in perks:
            for wline in _wrap_text(self.fonts["sans"], f"+ {perk}", max_w):
                canvas.blit(self.fonts["sans"].render(wline, True, settings.COLOR_TEXT), (text_x, y))
                y += 14

        y = max(y + 4, 101)
        canvas.blit(self.fonts["sans"].render("Trade-off:", True, WARN_COL), (text_x, y))
        y += 14
        for wline in _wrap_text(self.fonts["sans"], f"- {tradeoff}", max_w):
            canvas.blit(self.fonts["sans"].render(wline, True, settings.COLOR_MUTED), (text_x, y))
            y += 14

        canvas.set_clip(None)

    def _draw_care_tab(self, canvas: pygame.Surface) -> None:
        # Left care path selector
        for idx, (label, accent, _sub, _bullets) in enumerate(CARE_TOPICS):
            ry = 30 + idx * 28
            rect = pygame.Rect(6, ry, 82, 24)
            selected = idx == self.care_idx
            pygame.draw.rect(canvas, SEL_FILL if selected else settings.COLOR_PANEL, rect, border_radius=4)
            pygame.draw.rect(canvas, accent if selected else settings.COLOR_ACCENT, rect, 1, border_radius=4)
            lbl = self.fonts["sans"].render(label, True, accent if selected else settings.COLOR_MUTED)
            canvas.blit(lbl, (12, ry + 4))

        # Right care rules card
        label, accent, subtitle, bullets = CARE_TOPICS[self.care_idx]
        card = pygame.Rect(92, 28, 222, 116)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=5)
        pygame.draw.rect(canvas, accent, card, 1, border_radius=5)

        canvas.set_clip(card.inflate(-4, -4))
        text_x = card.x + 8
        max_w = card.w - 16

        canvas.blit(self.fonts["sans"].render(f"{label} Path", True, accent), (text_x, 33))
        canvas.blit(self.fonts["sans"].render(subtitle, True, settings.COLOR_MUTED), (text_x, 48))
        pygame.draw.line(canvas, (72, 54, 108), (text_x, 64), (card.right - 8, 64), 1)

        y = 69
        for i, line in enumerate(bullets):
            col = settings.COLOR_TEXT if i < 2 else settings.COLOR_ACCENT
            for wline in _wrap_text(self.fonts["sans"], line, max_w):
                canvas.blit(self.fonts["sans"].render(wline, True, col), (text_x, y))
                y += 16

        canvas.set_clip(None)

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill(settings.COLOR_BG)
        self._draw_top_tabs(canvas)

        if self.tab_idx == 0:
            self._draw_species_tab(canvas)
        elif self.tab_idx == 1:
            self._draw_traits_tab(canvas)
        else:
            self._draw_care_tab(canvas)

        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        foot = self.fonts["sans"].render("←/→:Tab   ↑/↓:Browse   Esc:Back", True, settings.COLOR_MUTED)
        canvas.blit(foot, ((settings.LOGICAL_WIDTH - foot.get_width()) // 2, 152))