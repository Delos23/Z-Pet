"""Pet Status / Profile screen for Z-Pet (320x170)."""

import pygame

import settings
from core.animator import PET_COLOR_PALETTES, load_species_animations
from core.pet import MAX_DAILY_TRAINS, MAX_LEVEL, Pet
from core.species import get_evolution_hint, get_personality, get_species

BAR_BG = (42, 32, 64)
XP_COL = (126, 206, 255)
GOLD_COL = (255, 224, 96)
GOOD_COL = (105, 225, 145)
WARN_COL = (245, 165, 95)

STAT_ROWS = [
    ("atk", "ATK", (240, 110, 125)),
    ("def", "DEF", (110, 185, 245)),
    ("spd", "SPD", (105, 225, 145)),
    ("int", "INT", (205, 150, 255)),
]


class StatusScene:
    """Displays species, personality, ability, stats, Arena records, and live care path."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict, pet: Pet):
        self.fonts = fonts
        self.config = config
        self.pet = pet
        self.species = get_species(pet.species_id)
        self.personality = get_personality(pet.species_id)

        sprite_dir = settings.SPRITES_DIR / pet.species_id
        self.animator = load_species_animations(
            sprite_dir,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=pet.color,
        )
        self.animator.play("idle", restart=True)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_g:
            return ("guide", {"return_to": "status", "pet": self.pet})
        if event.key in (pygame.K_ESCAPE, pygame.K_q, pygame.K_i, pygame.K_RETURN, pygame.K_SPACE):
            return ("home", {"pet": self.pet})
        return None

    def update(self, dt: float) -> None:
        self.animator.update(dt)

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill(settings.COLOR_BG)

        # Top header bar
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 24), (settings.LOGICAL_WIDTH, 24), 1)

        title_s = self.fonts["sans"].render(
            f"{self.pet.name} ({self.species['name']})", True, settings.COLOR_TEXT
        )
        canvas.blit(title_s, (8, 4))

        lvl_s = self.fonts["mono"].render(
            f"LV.{self.pet.level} {self.personality['label'].upper()}", True, GOLD_COL
        )
        canvas.blit(lvl_s, (settings.LOGICAL_WIDTH - lvl_s.get_width() - 8, 4))

        # Left pet card (portrait + stage/color + XP bar)
        left_card = pygame.Rect(8, 28, 92, 116)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, left_card, border_radius=5)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, left_card, 1, border_radius=5)

        pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(30, 86, 48, 8))
        canvas.blit(self.animator.get_frame(), (22, 28))

        col_lbl = PET_COLOR_PALETTES.get(self.pet.color, {}).get("label", "Purple")
        col_s = self.fonts["sans"].render(f"{self.pet.stage.upper()} {col_lbl}", True, settings.COLOR_MUTED)
        canvas.blit(col_s, (8 + (92 - col_s.get_width()) // 2, 96))

        if self.pet.level >= MAX_LEVEL:
            xp_txt = "XP MAX"
            xp_ratio = 1.0
        else:
            xp_txt = f"XP {self.pet.xp}/{self.pet.xp_to_next}"
            xp_ratio = min(1.0, self.pet.xp / max(1, self.pet.xp_to_next))

        xp_s = self.fonts["mono"].render(xp_txt, True, XP_COL)
        canvas.blit(xp_s, (8 + (92 - xp_s.get_width()) // 2, 112))
        pygame.draw.rect(canvas, BAR_BG, (16, 129, 76, 6))
        if xp_ratio > 0:
            pygame.draw.rect(canvas, XP_COL, (16, 129, int(76 * xp_ratio), 6))
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, (16, 129, 76, 6), 1)

        # Right stats, Arena records & care card
        right_card = pygame.Rect(106, 28, 206, 116)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, right_card, border_radius=5)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, right_card, 1, border_radius=5)

        canvas.set_clip(right_card.inflate(-4, -4))

        for idx, (stat_k, short_lbl, accent) in enumerate(STAT_ROWS):
            ry = 31 + idx * 13
            val = int(self.pet.battle_stats.get(stat_k, 5))
            canvas.blit(self.fonts["mono"].render(short_lbl, True, accent), (114, ry))

            bar_x, bar_y, bar_w, bar_h = 148, ry + 3, 122, 6
            pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h))
            fill_w = int(min(1.0, val / 150.0) * bar_w)
            if fill_w > 0:
                pygame.draw.rect(canvas, accent, (bar_x, bar_y, fill_w, bar_h))
            pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 1)

            val_s = self.fonts["mono"].render(f"{val:3d}", True, settings.COLOR_TEXT)
            canvas.blit(val_s, (276, ry))

        pygame.draw.line(canvas, (72, 54, 108), (114, 84), (304, 84), 1)

        # Care metrics (Bond, Mistakes, Drills left today)
        mst_col = WARN_COL if self.pet.care_mistakes >= 2 else settings.COLOR_MUTED
        meta_s = self.fonts["mono"].render(
            f"BND:{self.pet.bond} MST:{self.pet.care_mistakes} TRN:{self.pet.trainings_remaining}/{MAX_DAILY_TRAINS}",
            True,
            mst_col,
        )
        canvas.blit(meta_s, (114, 86))

        # Arena records (Boss Wins, Best Streak, Total Wins)
        boss_wins = int(getattr(self.pet, "boss_wins", 0))
        best_streak = int(getattr(self.pet, "best_streak", 0))
        battle_wins = int(getattr(self.pet, "battle_wins", 0))

        boss_s = self.fonts["mono"].render(f"BOSS:{boss_wins}", True, GOLD_COL)
        best_s = self.fonts["mono"].render(f"BEST:{best_streak}", True, XP_COL)
        wins_s = self.fonts["mono"].render(f"W:{battle_wins}", True, settings.COLOR_MUTED)

        canvas.blit(boss_s, (114, 99))
        canvas.blit(best_s, (114 + boss_s.get_width() + 10, 99))
        canvas.blit(wins_s, (304 - wins_s.get_width(), 99))

        # Active signature ability
        ab_txt = f"Skill: {self.pet.ability or 'None'}"
        ab_s = self.fonts["sans"].render(ab_txt, True, GOLD_COL)
        canvas.blit(ab_s, (114, 112))

        # Live care-driven evolution forecast
        hint_txt, hint_col = get_evolution_hint(self.pet)
        hint_s = self.fonts["sans"].render(hint_txt, True, hint_col)
        canvas.blit(hint_s, (114, 126))

        canvas.set_clip(None)

        # Bottom footer
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        foot = self.fonts["sans"].render("G:The Guide   Esc / I: Back to Room", True, settings.COLOR_MUTED)
        canvas.blit(foot, ((settings.LOGICAL_WIDTH - foot.get_width()) // 2, 152))