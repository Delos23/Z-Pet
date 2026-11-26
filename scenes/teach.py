"""Teach timing-drill scene for Z-Pet (320x170)."""

import pygame

import settings
from core import sound
from core.animator import load_species_animations
from core.display import KEYS_DOWN, KEYS_UP
from core.pet import MAX_DAILY_TRAINS, MAX_STAT, Pet
from core.save_manager import save_pet

BAR_BG = (42, 32, 64)
SEL_FILL = (76, 52, 122)
GOLD_COL = (255, 224, 96)
GOOD_COL = (105, 225, 145)
WARN_COL = (240, 95, 115)
CYAN_COL = (126, 206, 255)

STAT_DRILLS = [
    ("atk", "ATK", "Power Strikes", (240, 110, 125)),
    ("def", "DEF", "Max HP & Guard", (110, 185, 245)),
    ("spd", "SPD", "Turn Order & Crit", (105, 225, 145)),
    ("int", "INT", "Skills & SP Refund", (205, 150, 255)),
]


class TeachScene:
    """3-round timing-bar training drills to permanently raise ATK, DEF, SPD, or INT."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict, pet: Pet):
        self.fonts = fonts
        self.config = config
        self.pet = pet

        sprite_dir = settings.SPRITES_DIR / pet.species_id
        self.animator = load_species_animations(
            sprite_dir,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=pet.color,
        )
        self.animator.play("idle", restart=True)

        self.phase = "select"  # select -> drill -> result
        self.cursor_idx = 0
        self.round_num = 1
        self.total_rounds = 3
        self.drill_points = 0
        self.marker_pos = 0.0
        self.marker_dir = 1.0
        self.marker_speed = 1.45
        self.feedback_text = ""
        self.feedback_col = GOLD_COL
        self.feedback_timer = 0.0
        self.result: dict | None = None
        self.last_toast = ""
        sound.play_music("minigame")

    def _start_drill(self) -> None:
        self.phase = "drill"
        self.round_num = 1
        self.drill_points = 0
        self.marker_pos = 0.0
        self.marker_dir = 1.0
        self.marker_speed = 1.40
        self.feedback_text = ""
        self.feedback_timer = 0.0
        self.result = None
        self.animator.play("walk", restart=True)
        sound.play_music("minigame")

    def _judge_hit(self) -> None:
        dist = abs(self.marker_pos - 0.5)
        if dist <= 0.08:
            self.drill_points += 2
            self.feedback_text = "PERFECT! (+2)"
            self.feedback_col = GOLD_COL
            self.animator.play("happy", restart=True, next_anim="walk")
            sound.play("drill_perfect")
        elif dist <= 0.21:
            self.drill_points += 1
            self.feedback_text = "GOOD! (+1)"
            self.feedback_col = GOOD_COL
            self.animator.play("play", restart=True, next_anim="walk")
            sound.play("drill_good")
        else:
            self.feedback_text = "MISS (+0)"
            self.feedback_col = WARN_COL
            sound.play("drill_miss")

        self.feedback_timer = 0.55

    def _finish_drill(self) -> None:
        stat_key = STAT_DRILLS[self.cursor_idx][0]
        self.result = self.pet.apply_training(stat_key, self.drill_points)
        save_pet(self.pet)
        sound.stop_music()
        sound.play("level_up" if self.result.get("leveled_up") else "victory")
        self.phase = "result"
        self.animator.play("happy", restart=True, next_anim="idle")
        self.last_toast = (
            f"Trained {stat_key.upper()} +{self.result['stat_gain']}! +{self.result['xp_gain']} XP"
        )

    def on_exit(self) -> None:
        save_pet(self.pet)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if self.phase == "select":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                sound.play("back")
                return ("home", {"pet": self.pet})
            if event.key in KEYS_UP:
                self.cursor_idx = (self.cursor_idx - 1) % len(STAT_DRILLS)
                sound.play("click")
            elif event.key in KEYS_DOWN:
                self.cursor_idx = (self.cursor_idx + 1) % len(STAT_DRILLS)
                sound.play("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ok, msg = self.pet.can_train()
                if ok:
                    sound.play("select")
                    self._start_drill()
                else:
                    sound.play("error")
                    return ("home", {"pet": self.pet, "return_toast": msg})

        elif self.phase == "drill":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                sound.play("back")
                self.phase = "select"
                self.animator.play("idle", restart=True)
                return None
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.feedback_timer <= 0.0:
                self._judge_hit()

        elif self.phase == "result":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                sound.play("back")
                return ("home", {"pet": self.pet, "return_toast": self.last_toast, "return_anim": "happy"})
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ok, msg = self.pet.can_train()
                if ok:
                    sound.play("select")
                    self.phase = "select"
                    self.animator.play("idle", restart=True)
                    sound.play_music("minigame")
                else:
                    sound.play("error")
                    return ("home", {"pet": self.pet, "return_toast": msg, "return_anim": "happy"})
        return None

    def update(self, dt: float) -> None:
        self.animator.update(dt)

        if self.phase != "drill":
            return

        if self.feedback_timer > 0.0:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0.0:
                self.feedback_text = ""
                if self.round_num >= self.total_rounds:
                    self._finish_drill()
                else:
                    self.round_num += 1
                    self.marker_speed = 1.40 + (self.round_num - 1) * 0.35
                    self.marker_pos = 0.0 if self.round_num % 2 == 1 else 1.0
                    self.marker_dir = 1.0 if self.marker_pos == 0.0 else -1.0
            return

        self.marker_pos += self.marker_dir * self.marker_speed * dt
        if self.marker_pos >= 1.0:
            self.marker_pos = 1.0
            self.marker_dir = -1.0
        elif self.marker_pos <= 0.0:
            self.marker_pos = 0.0
            self.marker_dir = 1.0

    def _draw_footer(self, canvas: pygame.Surface, text: str) -> None:
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        foot_s = self.fonts["sans"].render(text, True, settings.COLOR_MUTED)
        canvas.blit(foot_s, ((settings.LOGICAL_WIDTH - foot_s.get_width()) // 2, 152))

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill(settings.COLOR_BG)

        # Header
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 24), (settings.LOGICAL_WIDTH, 24), 1)
        canvas.blit(self.fonts["sans"].render("TEACH DRILLS", True, GOLD_COL), (8, 4))
        rem_s = self.fonts["mono"].render(
            f"TODAY: {self.pet.trainings_remaining}/{MAX_DAILY_TRAINS}", True, CYAN_COL
        )
        canvas.blit(rem_s, (settings.LOGICAL_WIDTH - rem_s.get_width() - 8, 4))

        if self.phase == "select":
            # Left pet preview
            card = pygame.Rect(8, 30, 92, 112)
            pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=5)
            pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=5)
            pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(30, 96, 48, 8))
            canvas.blit(self.animator.get_frame(), (22, 38))
            lbl = self.fonts["sans"].render("Pick a Stat", True, settings.COLOR_MUTED)
            canvas.blit(lbl, (8 + (92 - lbl.get_width()) // 2, 116))

            # Right stat selector
            for idx, (stat_k, short_lbl, desc, accent) in enumerate(STAT_DRILLS):
                ry = 30 + idx * 28
                rect = pygame.Rect(106, ry, 206, 24)
                selected = idx == self.cursor_idx
                pygame.draw.rect(canvas, SEL_FILL if selected else settings.COLOR_PANEL, rect, border_radius=4)
                pygame.draw.rect(canvas, accent if selected else settings.COLOR_ACCENT, rect, 1, border_radius=4)

                val = int(self.pet.battle_stats.get(stat_k, 5))
                canvas.blit(self.fonts["mono"].render(f"{short_lbl}:{val:3d}", True, accent), (114, ry + 4))
                desc_s = self.fonts["sans"].render(desc, True, settings.COLOR_TEXT if selected else settings.COLOR_MUTED)
                canvas.blit(desc_s, (182, ry + 4))

            self._draw_footer(canvas, "↑/↓:Stat  Enter:Train  Esc:Back")
            return

        if self.phase == "drill":
            stat_k, short_lbl, _desc, accent = STAT_DRILLS[self.cursor_idx]

            rnd_s = self.fonts["mono"].render(
                f"ROUND {self.round_num}/{self.total_rounds}   {short_lbl} DRILL   PTS:{self.drill_points}",
                True,
                accent,
            )
            canvas.blit(rnd_s, ((settings.LOGICAL_WIDTH - rnd_s.get_width()) // 2, 30))

            pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(136, 98, 48, 8))
            canvas.blit(self.animator.get_frame(), (128, 40))

            # Timing bar with green GOOD zone and gold PERFECT center
            bar_x, bar_y, bar_w, bar_h = 26, 114, 268, 16
            pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)

            good_x = bar_x + int(bar_w * 0.29)
            good_w = int(bar_w * 0.42)
            pygame.draw.rect(canvas, (52, 138, 86), (good_x, bar_y + 1, good_w, bar_h - 2))

            perf_x = bar_x + int(bar_w * 0.42)
            perf_w = int(bar_w * 0.16)
            pygame.draw.rect(canvas, GOLD_COL, (perf_x, bar_y + 1, perf_w, bar_h - 2))

            pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

            # Moving marker needle
            mx = bar_x + int(self.marker_pos * (bar_w - 4))
            pygame.draw.rect(canvas, (255, 255, 255), (mx, bar_y - 3, 4, bar_h + 6), border_radius=1)

            if self.feedback_text:
                fb_s = self.fonts["sans"].render(self.feedback_text, True, self.feedback_col)
                canvas.blit(fb_s, ((settings.LOGICAL_WIDTH - fb_s.get_width()) // 2, 132))

            self._draw_footer(canvas, "Enter / Space: Stop Marker!   Esc:Cancel")
            return

        # Result modal
        if self.result is not None:
            res = self.result
            card = pygame.Rect(24, 28, 272, 114)
            pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
            pygame.draw.rect(canvas, GOLD_COL, card, 2, border_radius=6)

            head_s = self.fonts["title"].render(res["grade"], True, GOLD_COL)
            canvas.blit(head_s, ((settings.LOGICAL_WIDTH - head_s.get_width()) // 2, 34))

            st_line = f"{res['stat_key'].upper()}: {res['old_val']} -> {res['new_val']} (+{res['stat_gain']})"
            if res["new_val"] >= MAX_STAT:
                st_line += " MAX"
            st_s = self.fonts["mono"].render(st_line, True, GOOD_COL)
            canvas.blit(st_s, ((settings.LOGICAL_WIDTH - st_s.get_width()) // 2, 64))

            if res.get("leveled_up"):
                xp_line = f"LEVEL UP! Lv.{res['new_level']} (+{res['xp_gain']} XP)"
                xp_col = GOLD_COL
            else:
                xp_line = f"+{res['xp_gain']} XP   +{res['bond_gain']} Bond   +{res['happy_gain']} Happy"
                xp_col = CYAN_COL
            xp_s = self.fonts["sans"].render(xp_line, True, xp_col)
            canvas.blit(xp_s, ((settings.LOGICAL_WIDTH - xp_s.get_width()) // 2, 86))

            rem_s = self.fonts["sans"].render(
                f"Drills left today: {res['remaining_today']}/{MAX_DAILY_TRAINS}",
                True,
                settings.COLOR_MUTED,
            )
            canvas.blit(rem_s, ((settings.LOGICAL_WIDTH - rem_s.get_width()) // 2, 110))

        self._draw_footer(canvas, "Enter:Train Again   Esc:Home")