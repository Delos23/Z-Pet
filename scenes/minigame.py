"""Star Catch arcade mini-game scene for Z-Pet (320x170)."""

import math
import random
import pygame

import settings
from core import sound
from core.animator import load_species_animations
from core.display import KEYS_LEFT, KEYS_RIGHT
from core.pet import Pet
from core.save_manager import save_pet

ROUND_DURATION = 20.0
PET_SPEED = 148.0

GOLD_COL = (255, 224, 96)
MEGA_COL = (255, 118, 196)
BOLT_COL = (126, 212, 255)
GOOD_COL = (105, 225, 145)
WARN_COL = (240, 95, 115)


def _draw_star(surf: pygame.Surface, cx: int, cy: int, color: tuple, big: bool = False) -> None:
    r = 6 if big else 4
    pygame.draw.line(surf, color, (cx - r, cy), (cx + r, cy), 2)
    pygame.draw.line(surf, color, (cx, cy - r), (cx, cy + r), 2)
    pygame.draw.rect(surf, (255, 252, 225), (cx - 1, cy - 1, 3, 3))
    if big:
        pygame.draw.circle(surf, color, (cx, cy), 4, 1)


def _draw_bolt(surf: pygame.Surface, cx: int, cy: int) -> None:
    pts = [
        (cx + 2, cy - 6),
        (cx - 3, cy),
        (cx + 1, cy),
        (cx - 2, cy + 6),
        (cx + 4, cy - 1),
        (cx, cy - 1),
    ]
    pygame.draw.polygon(surf, BOLT_COL, pts)
    pygame.draw.polygon(surf, (255, 255, 255), pts, 1)


class StarCatchScene:
    """20-second Star Catch mini-game with combos, mega-stars, storm bolts, and full SFX."""

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
        self.rendered_size = settings.SPRITE_SIZE * settings.SPRITE_SCALE
        self.pet_y = 146 - self.rendered_size

        rng = random.Random(19)
        self.bg_stars = [
            (rng.randint(4, settings.LOGICAL_WIDTH - 4), rng.randint(24, 134), rng.uniform(0, 6.28))
            for _ in range(24)
        ]

        self.held_keys: set[int] = set()
        self.elapsed = 0.0
        self.result: dict | None = None
        self.last_toast = ""
        self._start_round()

    def _start_round(self) -> None:
        self.phase = "playing"
        self.time_left = ROUND_DURATION
        self.score = 0
        self.combo = 0
        self.stun_timer = 0.0
        self.spawn_timer = 0.35
        self.pet_x = float((settings.LOGICAL_WIDTH - self.rendered_size) // 2)
        self.items: list[dict] = []
        self.popups: list[dict] = []
        self.result = None
        self.animator.facing_left = False
        self.animator.play("idle", restart=True)
        sound.play_music("minigame")

    def _spawn_item(self) -> None:
        roll = random.random()
        if roll < 0.22:
            kind = "bolt"
            speed = random.uniform(76.0, 108.0)
        elif roll < 0.36:
            kind = "mega"
            speed = random.uniform(86.0, 118.0)
        else:
            kind = "star"
            speed = random.uniform(62.0, 94.0)

        self.items.append({
            "kind": kind,
            "x": float(random.randint(16, settings.LOGICAL_WIDTH - 16)),
            "y": 24.0,
            "vy": speed,
        })

    def _add_popup(self, text: str, x: float, y: float, color: tuple) -> None:
        self.popups.append({"text": text, "x": x, "y": y, "color": color, "life": 0.75})

    def _finish_round(self) -> None:
        self.phase = "result"
        self.held_keys.clear()
        self.result = self.pet.complete_minigame(self.score)
        save_pet(self.pet)
        sound.stop_music()
        sound.play("level_up" if self.result.get("leveled_up") else "victory")
        self.animator.play("happy", restart=True, next_anim="idle")
        if self.result.get("spd_bonus"):
            self.last_toast = f"Star Catch: {self.score} pts! +1 SPD!"
        else:
            self.last_toast = f"Star Catch: {self.score} pts! +{self.result['xp_gain']} XP"

    def on_exit(self) -> None:
        save_pet(self.pet)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type == pygame.KEYUP:
            self.held_keys.discard(event.key)
            return None

        if event.type != pygame.KEYDOWN:
            return None

        self.held_keys.add(event.key)

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            sound.play("back")
            if self.phase == "result":
                return ("home", {"pet": self.pet, "return_toast": self.last_toast, "return_anim": "happy"})
            return ("home", {"pet": self.pet, "return_toast": "Left Star Catch."})

        if self.phase == "result" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            ok, msg = self.pet.can_play()
            if ok:
                sound.play("select")
                self._start_round()
            else:
                sound.play("error")
                return ("home", {"pet": self.pet, "return_toast": msg, "return_anim": "idle"})
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt

        for p in self.popups:
            p["y"] -= 22.0 * dt
            p["life"] -= dt
        self.popups = [p for p in self.popups if p["life"] > 0]

        if self.phase != "playing":
            self.animator.update(dt)
            return

        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left <= 0.0:
            self._finish_round()
            return

        if self.stun_timer > 0.0:
            self.stun_timer = max(0.0, self.stun_timer - dt)
        else:
            move = 0.0
            if any(k in self.held_keys for k in KEYS_LEFT):
                move -= 1.0
            if any(k in self.held_keys for k in KEYS_RIGHT):
                move += 1.0

            if move != 0.0:
                self.pet_x += move * PET_SPEED * dt
                self.pet_x = max(2.0, min(float(settings.LOGICAL_WIDTH - self.rendered_size - 2), self.pet_x))
                self.animator.facing_left = move < 0
                self.animator.play("walk")
            elif not self.animator.is_playing_oneshot:
                self.animator.play("idle")

        self.animator.update(dt)

        # Spawn falling stars and storm bolts
        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self._spawn_item()
            self.spawn_timer = random.uniform(0.38, 0.65)

        catch_rect = pygame.Rect(
            int(self.pet_x) + 12,
            int(self.pet_y) + 16,
            self.rendered_size - 24,
            self.rendered_size - 18,
        )

        kept: list[dict] = []
        for item in self.items:
            item["y"] += item["vy"] * dt
            item_rect = pygame.Rect(int(item["x"]) - 6, int(item["y"]) - 6, 12, 12)

            if catch_rect.colliderect(item_rect):
                if item["kind"] == "bolt":
                    self.score = max(0, self.score - 1)
                    self.combo = 0
                    self.stun_timer = 0.55
                    sound.play("bolt")
                    self._add_popup("-1 ZAP!", item["x"] - 18, item["y"], WARN_COL)
                else:
                    self.combo += 1
                    base_pts = 3 if item["kind"] == "mega" else 1
                    combo_bonus = 1 if self.combo >= 5 else 0
                    pts = base_pts + combo_bonus
                    self.score += pts
                    self.animator.play("happy", restart=True, next_anim="idle")

                    if self.combo in (5, 10, 15, 20):
                        sound.play("combo")
                        self._add_popup(f"+{pts} x{self.combo}!", item["x"] - 14, item["y"], GOOD_COL)
                    elif item["kind"] == "mega":
                        sound.play("mega_catch")
                        self._add_popup(f"+{pts}!", item["x"] - 8, item["y"], MEGA_COL)
                    else:
                        sound.play("catch")
                        self._add_popup(f"+{pts}", item["x"] - 6, item["y"], GOLD_COL)
                continue

            if item["y"] < 146:
                kept.append(item)
            elif item["kind"] != "bolt":
                self.combo = 0
        self.items = kept

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill((18, 14, 38))

        for sx, sy, phase in self.bg_stars:
            col = (210, 200, 245) if math.sin(self.elapsed * 2.6 + phase) > 0.35 else (78, 66, 118)
            canvas.fill(col, (sx, sy, 1, 1))

        # Ground strip
        pygame.draw.rect(canvas, settings.COLOR_FLOOR, (0, 138, settings.LOGICAL_WIDTH, 10))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 138), (settings.LOGICAL_WIDTH, 138), 1)

        # Top HUD
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 22), (settings.LOGICAL_WIDTH, 22), 1)
        canvas.blit(self.fonts["sans"].render("STAR CATCH", True, GOLD_COL), (8, 3))

        score_txt = f"PTS:{self.score}"
        if self.combo >= 5:
            score_txt += f" x{self.combo}"
        sc_s = self.fonts["mono"].render(score_txt, True, GOOD_COL if self.combo >= 5 else settings.COLOR_TEXT)
        canvas.blit(sc_s, ((settings.LOGICAL_WIDTH - sc_s.get_width()) // 2, 3))

        time_col = WARN_COL if self.time_left <= 5.0 else BOLT_COL
        tm_s = self.fonts["mono"].render(f"{self.time_left:04.1f}s", True, time_col)
        canvas.blit(tm_s, (settings.LOGICAL_WIDTH - tm_s.get_width() - 8, 3))

        # Falling stars & bolts
        for item in self.items:
            ix, iy = int(item["x"]), int(item["y"])
            if item["kind"] == "bolt":
                _draw_bolt(canvas, ix, iy)
            elif item["kind"] == "mega":
                _draw_star(canvas, ix, iy, MEGA_COL, big=True)
            else:
                _draw_star(canvas, ix, iy, GOLD_COL, big=False)

        # Pet sprite (blinks briefly while stunned)
        if self.stun_timer <= 0.0 or int(self.elapsed * 16) % 2 == 0:
            pygame.draw.ellipse(canvas, (14, 10, 26), pygame.Rect(int(self.pet_x) + 14, 140, 36, 6))
            canvas.blit(self.animator.get_frame(), (int(self.pet_x), int(self.pet_y)))

        for p in self.popups:
            ps = self.fonts["mono"].render(p["text"], True, p["color"])
            canvas.blit(ps, (int(p["x"]), int(p["y"])))

        # Result modal
        if self.phase == "result" and self.result is not None:
            res = self.result
            card = pygame.Rect(24, 28, 272, 112)
            pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
            pygame.draw.rect(canvas, GOLD_COL, card, 2, border_radius=6)

            head = "NEW HIGH SCORE!" if res.get("is_new_best") else "TIME UP!"
            head_s = self.fonts["title"].render(head, True, GOLD_COL)
            canvas.blit(head_s, ((settings.LOGICAL_WIDTH - head_s.get_width()) // 2, 34))

            pts_s = self.fonts["mono"].render(
                f"Score: {res['score']}   Best: {res['high_score']}", True, settings.COLOR_TEXT
            )
            canvas.blit(pts_s, ((settings.LOGICAL_WIDTH - pts_s.get_width()) // 2, 64))

            if res.get("leveled_up"):
                rew_txt = f"LEVEL UP! Lv.{res['new_level']} (+{res['xp_gain']} XP)"
                rew_col = GOLD_COL
            else:
                rew_txt = f"+{res['happy_gain']} Happy  +{res['bond_gain']} Bond  +{res['xp_gain']} XP"
                rew_col = GOOD_COL
            rew_s = self.fonts["sans"].render(rew_txt, True, rew_col)
            canvas.blit(rew_s, ((settings.LOGICAL_WIDTH - rew_s.get_width()) // 2, 86))

            if res.get("spd_bonus"):
                spd_s = self.fonts["mono"].render("BONUS: +1 PERMANENT SPD!", True, MEGA_COL)
                canvas.blit(spd_s, ((settings.LOGICAL_WIDTH - spd_s.get_width()) // 2, 108))
            else:
                tip_s = self.fonts["sans"].render("Score 12+ for a +1 SPD bonus!", True, settings.COLOR_MUTED)
                canvas.blit(tip_s, ((settings.LOGICAL_WIDTH - tip_s.get_width()) // 2, 108))

        # Bottom footer
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        footer = (
            "Enter:Play Again   Esc:Home"
            if self.phase == "result"
            else "←/→:Move   Esc:Home"
        )
        foot_s = self.fonts["sans"].render(footer, True, settings.COLOR_MUTED)
        canvas.blit(foot_s, ((settings.LOGICAL_WIDTH - foot_s.get_width()) // 2, 152))