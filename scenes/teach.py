"""Teach Training Drill scene for Z-Pet (raises ATK, DEF, SPD, or INT with daily limit)."""

import pygame

import settings
from core.animator import load_species_animations
from core.pet import MAX_DAILY_TRAINS, Pet
from core.save_manager import save_pet
from core.display import KEYS_DOWN, KEYS_UP

SEL_FILL = (76, 52, 122)
BAR_BG = (42, 32, 64)
GOOD_COL = (105, 225, 145)
PERF_COL = (255, 224, 96)
MISS_COL = (240, 95, 115)
CURSOR_COL = (255, 255, 255)

STAT_DRILLS = [
    ("atk", "ATK", "Power Strike", (240, 110, 125)),
    ("def", "DEF", "Guard Wall",   (110, 185, 245)),
    ("spd", "SPD", "Quick Dash",   (105, 225, 145)),
    ("int", "INT", "Focus Spark",  (205, 150, 255)),
]

TOTAL_ROUNDS = 3


class TeachScene:
    """Pick a battle stat and complete a 3-round timing drill to boost it."""

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
        self.drill_points = 0
        self.marker_pos = 0.0
        self.marker_dir = 1.0
        self.marker_speed = 1.15
        self.pause_timer = 0.0
        self.feedback_text = ""
        self.feedback_col = GOOD_COL
        self.result: dict | None = None
        self.last_reward_toast = ""

    def _start_drill(self) -> None:
        self.phase = "drill"
        self.round_num = 1
        self.drill_points = 0
        self.result = None
        self._setup_round()

    def _setup_round(self) -> None:
        self.marker_pos = 0.02 if self.round_num % 2 == 1 else 0.98
        self.marker_dir = 1.0 if self.round_num % 2 == 1 else -1.0
        self.marker_speed = 1.1 + (self.round_num - 1) * 0.28
        self.pause_timer = 0.0
        self.feedback_text = ""
        self.animator.play("walk", restart=True)

    def _zone_widths(self) -> tuple[float, float]:
        good_half = max(0.11, 0.17 - (self.round_num - 1) * 0.025)
        perf_half = max(0.04, 0.065 - (self.round_num - 1) * 0.01)
        return good_half, perf_half

    def _evaluate_hit(self) -> None:
        dist = abs(self.marker_pos - 0.5)
        good_half, perf_half = self._zone_widths()

        if dist <= perf_half:
            self.drill_points += 2
            self.feedback_text = "PERFECT! +2"
            self.feedback_col = PERF_COL
            self.animator.play("happy", restart=True, next_anim="idle")
        elif dist <= good_half:
            self.drill_points += 1
            self.feedback_text = "GOOD! +1"
            self.feedback_col = GOOD_COL
            self.animator.play("play", restart=True, next_anim="idle")
        else:
            self.feedback_text = "MISS!"
            self.feedback_col = MISS_COL
            self.animator.play("idle", restart=True)

        self.pause_timer = 0.65

    def _finish_drill(self) -> None:
        stat_key = STAT_DRILLS[self.cursor_idx][0]
        self.result = self.pet.apply_training(stat_key, self.drill_points)
        save_pet(self.pet)
        self.phase = "result"
        self.animator.play("happy", restart=True, next_anim="idle")
        self.last_reward_toast = (
            f"{stat_key.upper()} +{self.result['stat_gain']}! "
            f"({self.result['remaining_today']}/{MAX_DAILY_TRAINS} left)"
        )

    def on_exit(self) -> None:
        save_pet(self.pet)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if self.phase == "select":
            if event.key in KEYS_UP:
             self.cursor_idx = (self.cursor_idx - 1) % len(STAT_DRILLS)
            elif event.key in KEYS_DOWN:
             self.cursor_idx = (self.cursor_idx + 1) % len(STAT_DRILLS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
             self.cursor_idx = (self.cursor_idx + 1) % len(STAT_DRILLS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ok, msg = self.pet.can_train()
                if ok:
                    self._start_drill()
                else:
                    return ("home", {"pet": self.pet, "return_toast": msg})

        elif self.phase == "drill":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.phase = "select"
                self.animator.play("idle", restart=True)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN) and self.pause_timer <= 0:
                self._evaluate_hit()

        elif self.phase == "result":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return (
                    "home",
                    {
                        "pet": self.pet,
                        "return_toast": self.last_reward_toast,
                        "return_anim": "happy",
                    },
                )
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ok, msg = self.pet.can_train()
                if ok:
                    self.phase = "select"
                    self.animator.play("idle", restart=True)
                else:
                    return (
                        "home",
                        {
                            "pet": self.pet,
                            "return_toast": msg,
                            "return_anim": "happy",
                        },
                    )
        return None

    def update(self, dt: float) -> None:
        self.animator.update(dt)

        if self.phase == "drill":
            if self.pause_timer > 0:
                self.pause_timer -= dt
                if self.pause_timer <= 0:
                    if self.round_num < TOTAL_ROUNDS:
                        self.round_num += 1
                        self._setup_round()
                    else:
                        self._finish_drill()
            else:
                self.marker_pos += self.marker_dir * self.marker_speed * dt
                if self.marker_pos >= 1.0:
                    self.marker_pos = 1.0
                    self.marker_dir = -1.0
                elif self.marker_pos <= 0.0:
                    self.marker_pos = 0.0
                    self.marker_dir = 1.0

    def _draw_top_bar(self, canvas: pygame.Surface, left_txt: str, right_txt: str, right_col: tuple) -> None:
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 24), (settings.LOGICAL_WIDTH, 24), 1)

        left_s = self.fonts["sans"].render(left_txt, True, settings.COLOR_TEXT)
        right_s = self.fonts["mono"].render(right_txt, True, right_col)
        canvas.blit(left_s, (8, 4))
        canvas.blit(right_s, (settings.LOGICAL_WIDTH - right_s.get_width() - 8, 4))

    def _draw_footer(self, canvas: pygame.Surface, text: str) -> None:
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        surf = self.fonts["sans"].render(text, True, settings.COLOR_MUTED)
        canvas.blit(surf, ((settings.LOGICAL_WIDTH - surf.get_width()) // 2, 152))

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill(settings.COLOR_BG)

        if self.phase == "select":
            rem = self.pet.trainings_remaining
            rem_col = GOOD_COL if rem > 0 else MISS_COL
            self._draw_top_bar(
                canvas,
                f"TEACH {self.pet.name}",
                f"LEFT:{rem}/{MAX_DAILY_TRAINS}  ENG:{int(self.pet.energy)}%",
                rem_col,
            )

            for idx, (stat_key, short_lbl, drill_name, accent) in enumerate(STAT_DRILLS):
                row_y = 32 + idx * 28
                row_rect = pygame.Rect(12, row_y, 296, 24)
                selected = idx == self.cursor_idx

                if selected:
                    pygame.draw.rect(canvas, SEL_FILL, row_rect, border_radius=4)
                    pygame.draw.rect(canvas, accent, row_rect, 1, border_radius=4)
                else:
                    pygame.draw.rect(canvas, settings.COLOR_PANEL, row_rect, border_radius=4)

                tag = self.fonts["mono"].render(short_lbl, True, accent)
                canvas.blit(tag, (22, row_y + 4))

                name_s = self.fonts["sans"].render(
                    drill_name, True, settings.COLOR_TEXT if selected else settings.COLOR_MUTED
                )
                canvas.blit(name_s, (62, row_y + 4))

                val = int(self.pet.battle_stats.get(stat_key, 5))
                bar_x, bar_y, bar_w, bar_h = 194, row_y + 8, 72, 8
                pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h))
                fill_w = int(min(1.0, val / 150.0) * bar_w)
                if fill_w > 0:
                    pygame.draw.rect(canvas, accent, (bar_x, bar_y, fill_w, bar_h))
                pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 1)

                val_s = self.fonts["mono"].render(f"{val:3d}", True, settings.COLOR_TEXT)
                canvas.blit(val_s, (272, row_y + 4))

            self._draw_footer(canvas, "↑/↓:Stat  Enter:Train  Esc:Back")

        elif self.phase == "drill":
            _, short_lbl, drill_name, accent = STAT_DRILLS[self.cursor_idx]
            self._draw_top_bar(
                canvas,
                f"{short_lbl}: {drill_name}",
                f"RD {self.round_num}/{TOTAL_ROUNDS}  PTS:{self.drill_points}",
                accent,
            )

            pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(136, 86, 48, 8))
            canvas.blit(self.animator.get_frame(), (128, 28))

            if self.feedback_text:
                fb = self.fonts["sans"].render(self.feedback_text, True, self.feedback_col)
                canvas.blit(fb, ((settings.LOGICAL_WIDTH - fb.get_width()) // 2, 92))

            bar_x, bar_y, bar_w, bar_h = 26, 112, 268, 22
            pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)

            good_half, perf_half = self._zone_widths()
            good_x = bar_x + int((0.5 - good_half) * bar_w)
            good_w = int(good_half * 2 * bar_w)
            pygame.draw.rect(canvas, GOOD_COL, (good_x, bar_y + 2, good_w, bar_h - 4))

            perf_x = bar_x + int((0.5 - perf_half) * bar_w)
            perf_w = int(perf_half * 2 * bar_w)
            pygame.draw.rect(canvas, PERF_COL, (perf_x, bar_y + 2, perf_w, bar_h - 4))

            pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)

            mx = bar_x + int(self.marker_pos * (bar_w - 6))
            pygame.draw.rect(canvas, (20, 14, 30), (mx - 1, bar_y - 3, 8, bar_h + 6), border_radius=2)
            pygame.draw.rect(canvas, CURSOR_COL, (mx, bar_y - 2, 6, bar_h + 4), border_radius=2)

            self._draw_footer(canvas, "Space / Enter: Hit Center!   Esc:Back")

        elif self.phase == "result" and self.result is not None:
            res = self.result
            stat_lbl = res["stat_key"].upper()
            rem = res["remaining_today"]
            self._draw_top_bar(canvas, "DRILL COMPLETE", f"SCORE {self.drill_points}/6", PERF_COL)

            card = pygame.Rect(20, 32, 280, 108)
            pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
            pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=6)

            canvas.blit(self.animator.get_frame(), (28, 52))

            grade_col = PERF_COL if res["grade"] == "PERFECT!" else GOOD_COL
            grade_s = self.fonts["title"].render(res["grade"], True, grade_col)
            canvas.blit(grade_s, (104, 40))

            stat_s = self.fonts["mono"].render(
                f"{stat_lbl}: {res['old_val']} -> {res['new_val']} (+{res['stat_gain']})",
                True,
                settings.COLOR_TEXT,
            )
            canvas.blit(stat_s, (104, 72))

            if res.get("leveled_up"):
                bonus_txt = f"LEVEL UP! Lv.{res['new_level']} (+{res['xp_gain']} XP)"
                bonus_col = PERF_COL
            else:
                bonus_txt = f"+{res['xp_gain']} XP   +{res['bond_gain']} Bond"
                bonus_col = settings.COLOR_ACCENT
            bonus_s = self.fonts["sans"].render(bonus_txt, True, bonus_col)
            canvas.blit(bonus_s, (104, 94))

            rem_txt = f"Daily drills left: {rem}/{MAX_DAILY_TRAINS}"
            rem_s = self.fonts["sans"].render(rem_txt, True, GOOD_COL if rem > 0 else MISS_COL)
            canvas.blit(rem_s, (104, 114))

            footer = "Enter:Train Again   Esc:Home" if rem > 0 else "Daily limit reached!  Esc:Home"
            self._draw_footer(canvas, footer)