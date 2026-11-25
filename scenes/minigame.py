"""Star Catch interactive Play mini-game for Z-Pet (320x170)."""

import math
import random
import pygame

import settings
from core.animator import load_species_animations
from core.pet import Pet
from core.save_manager import save_pet

ROUND_SECONDS = 20.0
PET_SPEED = 148.0

STAR_GOLD = (255, 232, 102)
STAR_PINK = (255, 115, 195)
STAR_CORE = (255, 250, 225)
BOLT_OUT = (240, 82, 108)
BOLT_CORE = (255, 212, 120)
GOOD_COL = (105, 225, 145)
WARN_COL = (245, 195, 85)


def draw_star(canvas: pygame.Surface, cx: int, cy: int, outer_col: tuple, size: int = 4) -> None:
    """Draws a crisp pixel star centered at (cx, cy)."""
    pygame.draw.rect(canvas, outer_col, (cx - 1, cy - size, 3, size * 2 + 1))
    pygame.draw.rect(canvas, outer_col, (cx - size, cy - 1, size * 2 + 1, 3))
    pygame.draw.rect(canvas, STAR_CORE, (cx - 1, cy - 1, 3, 3))


def draw_bolt(canvas: pygame.Surface, cx: int, cy: int) -> None:
    """Draws a falling hazard zap-orb."""
    pygame.draw.circle(canvas, BOLT_OUT, (cx, cy), 5)
    pygame.draw.rect(canvas, BOLT_CORE, (cx - 1, cy - 3, 2, 3))
    pygame.draw.rect(canvas, BOLT_CORE, (cx, cy, 2, 3))


class StarCatchScene:
    """20-second arcade mini-game: move Sparkkit left/right to catch stars & dodge zaps."""

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
        self.rendered_size = settings.SPRITE_SIZE * settings.SPRITE_SCALE  # 64px

        rng = random.Random(99)
        self.bg_stars = [
            (rng.randint(4, settings.LOGICAL_WIDTH - 4), rng.randint(28, 126), rng.uniform(0, 6.28))
            for _ in range(22)
        ]

        self.held_keys: set[int] = set()
        self.elapsed = 0.0
        self.last_reward_toast = ""
        self._reset_round()

    def _reset_round(self) -> None:
        self.phase = "playing"  # playing -> result
        self.time_left = ROUND_SECONDS
        self.score = 0
        self.combo = 0
        self.pet_x = float((settings.LOGICAL_WIDTH - self.rendered_size) // 2)
        self.pet_y = 138 - 56  # Feet sit neatly on the y=136 floor
        self.stun_timer = 0.0
        self.spawn_timer = 0.45
        self.items: list[dict] = []
        self.popups: list[dict] = []
        self.result: dict | None = None
        self.held_keys.clear()
        self.animator.play("idle", restart=True)

    def _spawn_item(self) -> None:
        roll = random.random()
        if roll < 0.22:
            kind = "bolt"
            speed = random.uniform(76.0, 108.0)
        elif roll < 0.36:
            kind = "mega"
            speed = random.uniform(82.0, 112.0)
        else:
            kind = "star"
            speed = random.uniform(62.0, 92.0)

        self.items.append({
            "kind": kind,
            "x": float(random.randint(18, settings.LOGICAL_WIDTH - 18)),
            "y": 26.0,
            "vy": speed,
        })

    def _add_popup(self, text: str, x: float, y: float, color: tuple) -> None:
        self.popups.append({"text": text, "x": x, "y": y, "color": color, "life": 0.75})

    def _finish_round(self) -> None:
        self.phase = "result"
        self.held_keys.clear()
        self.result = self.pet.complete_minigame(self.score)
        save_pet(self.pet)
        self.animator.play("happy", restart=True, next_anim="idle")
        self.last_reward_toast = (
            f"Star Catch: {self.score}pts! +{self.result['happy_gain']} Happy"
        )

    def on_exit(self) -> None:
        save_pet(self.pet)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type == pygame.KEYUP:
            self.held_keys.discard(event.key)
            return None

        if event.type != pygame.KEYDOWN:
            return None

        if self.phase == "playing":
            self.held_keys.add(event.key)
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return ("home", {"pet": self.pet})

        elif self.phase == "result":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return (
                    "home",
                    {
                        "pet": self.pet,
                        "return_toast": self.last_reward_toast,
                        "return_anim": "play",
                    },
                )
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ok, msg = self.pet.can_play()
                if ok:
                    self._reset_round()
                else:
                    return (
                        "home",
                        {
                            "pet": self.pet,
                            "return_toast": msg,
                            "return_anim": "idle",
                        },
                    )
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt

        for p in self.popups:
            p["y"] -= 24.0 * dt
            p["life"] -= dt
        self.popups = [p for p in self.popups if p["life"] > 0]

        if self.phase != "playing":
            self.animator.update(dt)
            return

        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0.0
            self._finish_round()
            return

        # Movement (uses held_keys so it works identically on PC and Cardputer Zero evdev)
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.animator.play("idle")
        else:
            move = 0.0
            if pygame.K_LEFT in self.held_keys or pygame.K_a in self.held_keys:
                move -= 1.0
            if pygame.K_RIGHT in self.held_keys or pygame.K_d in self.held_keys:
                move += 1.0

            if move != 0.0:
                self.pet_x += move * PET_SPEED * dt
                self.pet_x = max(-8.0, min(settings.LOGICAL_WIDTH - self.rendered_size + 8.0, self.pet_x))
                self.animator.facing_left = move < 0
                if not self.animator.is_playing_oneshot:
                    self.animator.play("walk")
            elif not self.animator.is_playing_oneshot:
                self.animator.play("idle")

        self.animator.update(dt)

        # Spawn falling stars & storm bolts (slightly faster in the final 8 seconds)
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self._spawn_item()
            self.spawn_timer = random.uniform(0.38, 0.62) if self.time_left < 8.0 else random.uniform(0.48, 0.78)

        # Forgiving catch box vs tighter hazard box
        catch_rect = pygame.Rect(int(self.pet_x) + 14, int(self.pet_y) + 20, 36, 36)
        dodge_rect = pygame.Rect(int(self.pet_x) + 20, int(self.pet_y) + 26, 24, 28)

        survivors: list[dict] = []
        for item in self.items:
            item["y"] += item["vy"] * dt
            if item["y"] > 142:
                if item["kind"] in ("star", "mega"):
                    self.combo = 0
                continue

            item_rect = pygame.Rect(int(item["x"]) - 5, int(item["y"]) - 5, 10, 10)
            if item["kind"] == "bolt":
                if dodge_rect.colliderect(item_rect) and self.stun_timer <= 0:
                    self.score = max(0, self.score - 1)
                    self.combo = 0
                    self.stun_timer = 0.35
                    self._add_popup("ZAP! -1", item["x"] - 18, item["y"] - 8, BOLT_OUT)
                    continue
            else:
                if catch_rect.colliderect(item_rect):
                    self.combo += 1
                    pts = 3 if item["kind"] == "mega" else 1
                    if self.combo >= 5:
                        pts += 1
                    self.score += pts
                    col = STAR_PINK if item["kind"] == "mega" else STAR_GOLD
                    label = f"+{pts}!" if self.combo >= 5 else f"+{pts}"
                    self._add_popup(label, item["x"] - 8, item["y"] - 8, col)
                    self.animator.play("happy", restart=True, next_anim="idle")
                    continue

            survivors.append(item)
        self.items = survivors

    def render(self, canvas: pygame.Surface) -> None:
        # Brief subtle red tint if zapped
        bg = (44, 18, 36) if self.stun_timer > 0 else settings.COLOR_BG
        canvas.fill(bg)

        # Twinkling sky stars
        for sx, sy, phase in self.bg_stars:
            col = (210, 200, 245) if math.sin(self.elapsed * 2.5 + phase) > 0.3 else (96, 84, 138)
            canvas.fill(col, (sx, sy, 1, 1))

        # Floor strip
        pygame.draw.rect(canvas, settings.COLOR_FLOOR, (0, 136, settings.LOGICAL_WIDTH, 12))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 136), (settings.LOGICAL_WIDTH, 136), 1)

        # Top HUD bar
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 24), (settings.LOGICAL_WIDTH, 24), 1)

        title_s = self.fonts["sans"].render("STAR CATCH", True, settings.COLOR_TEXT)
        canvas.blit(title_s, (8, 4))

        combo_txt = f" x{self.combo}" if self.combo >= 3 else ""
        score_s = self.fonts["mono"].render(f"PTS:{self.score}{combo_txt}", True, STAR_GOLD)
        canvas.blit(score_s, ((settings.LOGICAL_WIDTH - score_s.get_width()) // 2, 4))

        time_col = BOLT_OUT if self.time_left <= 5.0 else GOOD_COL
        time_s = self.fonts["mono"].render(f"{int(math.ceil(self.time_left)):02d}s", True, time_col)
        canvas.blit(time_s, (settings.LOGICAL_WIDTH - time_s.get_width() - 8, 4))

        # Falling stars & bolts
        for item in self.items:
            ix, iy = int(item["x"]), int(item["y"])
            if item["kind"] == "star":
                draw_star(canvas, ix, iy, STAR_GOLD, size=4)
            elif item["kind"] == "mega":
                draw_star(canvas, ix, iy, STAR_PINK, size=5)
            else:
                draw_bolt(canvas, ix, iy)

        # Sparkkit shadow + sprite (flickers gently while stunned)
        if self.stun_timer <= 0 or int(self.elapsed * 20) % 2 == 0:
            pygame.draw.ellipse(canvas, (18, 12, 28), pygame.Rect(int(self.pet_x) + 14, 134, 36, 6))
            canvas.blit(self.animator.get_frame(), (int(self.pet_x), int(self.pet_y)))

        # Floating score popups
        for p in self.popups:
            surf = self.fonts["mono"].render(p["text"], True, p["color"])
            canvas.blit(surf, (int(p["x"]), int(p["y"])))

        # Result overlay when time is up
        if self.phase == "result" and self.result is not None:
            res = self.result
            card = pygame.Rect(24, 32, 272, 106)
            pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
            pygame.draw.rect(canvas, settings.COLOR_ACCENT, card, 1, border_radius=6)

            head_txt = "NEW BEST!" if res["is_new_best"] else "TIME UP!"
            head_col = STAR_GOLD if res["is_new_best"] else settings.COLOR_TEXT
            head_s = self.fonts["title"].render(head_txt, True, head_col)
            canvas.blit(head_s, ((settings.LOGICAL_WIDTH - head_s.get_width()) // 2, 38))

            sc_s = self.fonts["mono"].render(
                f"Score: {res['score']}   Best: {res['high_score']}",
                True,
                settings.COLOR_TEXT,
            )
            canvas.blit(sc_s, ((settings.LOGICAL_WIDTH - sc_s.get_width()) // 2, 68))

            rew_txt = f"+{res['happy_gain']} Happy   +{res['bond_gain']} Bond"
            if res["spd_bonus"]:
                rew_txt += f"   +{res['spd_bonus']} SPD!"
            rew_s = self.fonts["sans"].render(rew_txt, True, GOOD_COL)
            canvas.blit(rew_s, ((settings.LOGICAL_WIDTH - rew_s.get_width()) // 2, 92))

            if res.get("leveled_up"):
                xp_txt = f"LEVEL UP! Now Lv.{res['new_level']} (+{res['xp_gain']} XP)"
                xp_col = STAR_GOLD
            else:
                xp_txt = f"+{res['xp_gain']} XP   Energy: {int(self.pet.energy)}%"
                xp_col = settings.COLOR_MUTED
            eng_s = self.fonts["sans"].render(xp_txt, True, xp_col)
            canvas.blit(eng_s, ((settings.LOGICAL_WIDTH - eng_s.get_width()) // 2, 112))

        # Bottom controls bar
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        footer = (
            "Enter:Play Again   Esc:Home"
            if self.phase == "result"
            else "A/D or Lt/Rt: Move   Esc:Home"
        )
        foot_s = self.fonts["sans"].render(footer, True, settings.COLOR_MUTED)
        canvas.blit(foot_s, ((settings.LOGICAL_WIDTH - foot_s.get_width()) // 2, 152))