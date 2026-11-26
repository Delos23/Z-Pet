"""Turn-based Battle Arena scene for Z-Pet with Elite Boss challenges every 5th streak fight."""

import math
import random
import pygame

import settings
from core.abilities import (
    effective_stat,
    is_boss_fight,
    make_fighter_from_pet,
    resolve_action,
    spawn_wild_rival,
)
from core.animator import load_species_animations
from core.display import KEYS_LEFT, KEYS_RIGHT
from core.pet import Pet
from core.save_manager import save_pet

BAR_BG = (42, 32, 64)
HP_GOOD = (105, 225, 145)
HP_WARN = (245, 195, 85)
HP_LOW = (240, 95, 115)
SP_ON = (255, 224, 96)
SP_OFF = (70, 56, 98)
SEL_FILL = (84, 56, 136)
SLOT_BG = (34, 24, 54)
SLOT_BORDER = (72, 54, 108)
DISABLED_COL = (100, 90, 128)
CYAN_COL = (126, 206, 255)

BOSS_BG = (34, 14, 38)
BOSS_PANEL = (54, 22, 58)
BOSS_GOLD = (255, 208, 74)
BOSS_CRIMSON = (232, 72, 102)

COMMANDS = [
    ("strike", "Strike"),
    ("skill",  "Skill"),
    ("guard",  "Guard"),
    ("flee",   "Flee"),
]


def draw_boss_crown(surf: pygame.Surface, x: int, y: int) -> None:
    """Draws a crisp 9x7 pixel-art gold crown for Elite Boss badges."""
    gold = BOSS_GOLD
    hi = (255, 248, 190)
    gem = BOSS_CRIMSON
    pattern = [
        "#...#...#",
        "##.###.##",
        "#########",
        "#.G###G.#",
        "#########",
        ".HHHHHHH.",
    ]
    for r, row in enumerate(pattern):
        for c, ch in enumerate(row):
            if ch == "#":
                surf.set_at((x + c, y + r), gold)
            elif ch == "H":
                surf.set_at((x + c, y + r), hi)
            elif ch == "G":
                surf.set_at((x + c, y + r), gem)


class BattleScene:
    """Turn-based arena pitting the player's Z-Pet against wild Z-Pets & Elite Bosses."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict, pet: Pet):
        self.fonts = fonts
        self.config = config
        self.pet = pet

        rng = random.Random(31)
        self.stars = [
            (rng.randint(4, settings.LOGICAL_WIDTH - 4), rng.randint(28, 106), rng.uniform(0, 6.28))
            for _ in range(20)
        ]

        self.elapsed = 0.0
        self.last_toast = ""
        self._start_match()

    def _start_match(self) -> None:
        self.player = make_fighter_from_pet(self.pet)
        self.is_boss = is_boss_fight(self.pet.win_streak)
        self.rival = spawn_wild_rival(
            self.pet.level,
            exclude_species=self.pet.species_id,
            is_boss=self.is_boss,
            streak=self.pet.win_streak,
        )

        self.player_anim = load_species_animations(
            settings.SPRITES_DIR / self.player["species_id"],
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=self.player["color"],
        )
        self.player_anim.facing_left = False
        self.player_anim.play("idle", restart=True)

        self.rival_anim = load_species_animations(
            settings.SPRITES_DIR / self.rival["species_id"],
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=self.rival["color"],
        )
        self.rival_anim.facing_left = True
        self.rival_anim.play("idle", restart=True)

        self.phase = "choose"  # choose -> executing -> result
        self.cmd_idx = 0
        self.turn_queue: list[tuple[str, str]] = []
        self.step_timer = 0.0

        if self.is_boss:
            self.log_text = (
                f"ELITE {self.rival['boss_title']} {self.rival['name']} Lv.{self.rival['level']}!"
            )
        else:
            self.log_text = f"Wild {self.rival['name']} Lv.{self.rival['level']} appeared!"

        self.result_info: dict | None = None
        self.p_lunge = 0.0
        self.r_lunge = 0.0
        self.p_shake = 0.0
        self.r_shake = 0.0
        self.popups: list[dict] = []

    def _add_popup(self, text: str, x: float, y: float, color: tuple) -> None:
        self.popups.append({"text": text, "x": x, "y": y, "color": color, "life": 0.95})

    def _pick_rival_action(self) -> str:
        if self.is_boss:
            if self.rival["sp"] >= 2 and random.random() < 0.85:
                return "skill"
            if (
                self.rival["hp"] < self.rival["max_hp"] * 0.45
                and self.player["sp"] >= 2
                and random.random() < 0.35
            ):
                return "guard"
            return "strike"

        if self.rival["sp"] >= 2 and random.random() < 0.75:
            return "skill"
        if self.rival["hp"] < self.rival["max_hp"] * 0.35 and random.random() < 0.35:
            return "guard"
        return "strike"

    def _queue_turn(self, player_action: str) -> None:
        rival_action = self._pick_rival_action()
        self.player["guarding"] = False
        self.rival["guarding"] = False

        p_prio = 2 if player_action == "guard" else (
            1 if (player_action == "skill" and self.player["ability_fx"].get("priority")) else 0
        )
        r_prio = 2 if rival_action == "guard" else (
            1 if (rival_action == "skill" and self.rival["ability_fx"].get("priority")) else 0
        )

        p_spd = effective_stat(self.player, "spd")
        r_spd = effective_stat(self.rival, "spd")

        if (p_prio, p_spd) >= (r_prio, r_spd):
            self.turn_queue = [("player", player_action), ("rival", rival_action), ("dot", "tick")]
        else:
            self.turn_queue = [("rival", rival_action), ("player", player_action), ("dot", "tick")]

        self.phase = "executing"
        self.step_timer = 0.05

    def _run_next_step(self) -> None:
        if self.player["hp"] <= 0 or self.rival["hp"] <= 0:
            self._finish_battle()
            return

        if not self.turn_queue:
            self.phase = "choose"
            return

        actor, action = self.turn_queue.pop(0)

        if actor == "dot":
            msgs = []
            for side, f, px in (("player", self.player, 68), ("rival", self.rival, 250)):
                if f["hp"] > 0 and f["dot_turns"] > 0:
                    dmg = max(3, int(f["max_hp"] * 0.08))
                    f["hp"] = max(0, f["hp"] - dmg)
                    f["dot_turns"] -= 1
                    self._add_popup(f"-{dmg}", px, 72, HP_WARN)
                    if side == "player":
                        self.p_shake = 0.25
                    else:
                        self.r_shake = 0.25
                    msgs.append(f"{f['dot_label']} hit {f['name']} -{dmg}!")
            if msgs:
                self.log_text = msgs[0]
                self.step_timer = 0.75
            else:
                self.phase = "choose"
            if self.player["hp"] <= 0 or self.rival["hp"] <= 0:
                self.turn_queue.clear()
                self.step_timer = 0.7
            return

        if actor == "player":
            res = resolve_action(self.player, self.rival, action)
            self.log_text = res["message"]
            if action != "guard":
                self.p_lunge = 0.22
                self.player_anim.play("play" if action == "skill" else "happy", restart=True, next_anim="idle")
                if res["dodged"]:
                    self._add_popup("DODGE!", 228, 70, CYAN_COL)
                elif res["damage"] > 0:
                    self.r_shake = 0.28
                    col = SP_ON if res["crit"] else HP_LOW
                    self._add_popup(f"-{res['damage']}", 244, 72, col)
            if res["healed"] > 0:
                self._add_popup(f"+{res['healed']}", 60, 68, HP_GOOD)
            if res["reflected"] > 0:
                self.p_shake = 0.25
                self._add_popup(f"-{res['reflected']}", 62, 82, HP_WARN)
        else:
            res = resolve_action(self.rival, self.player, action)
            self.log_text = res["message"]
            if action != "guard":
                self.r_lunge = 0.22
                self.rival_anim.play("play" if action == "skill" else "happy", restart=True, next_anim="idle")
                if res["dodged"]:
                    self._add_popup("DODGE!", 48, 70, CYAN_COL)
                elif res["damage"] > 0:
                    self.p_shake = 0.28
                    col = SP_ON if res["crit"] else HP_LOW
                    self._add_popup(f"-{res['damage']}", 62, 72, col)
            if res["healed"] > 0:
                self._add_popup(f"+{res['healed']}", 242, 68, HP_GOOD)
            if res["reflected"] > 0:
                self.r_shake = 0.25
                self._add_popup(f"-{res['reflected']}", 244, 82, HP_WARN)

        self.step_timer = 0.95
        if self.player["hp"] <= 0 or self.rival["hp"] <= 0:
            self.turn_queue.clear()

    def _finish_battle(self) -> None:
        won = self.rival["hp"] <= 0 and self.player["hp"] > 0
        self.result_info = self.pet.complete_battle(
            won=won,
            enemy_level=self.rival["level"],
            is_boss=self.is_boss,
        )
        save_pet(self.pet)
        self.phase = "result"
        if won:
            self.player_anim.play("happy", restart=True, next_anim="idle")
            if self.is_boss and self.result_info.get("stat_reward"):
                st_k, st_v = self.result_info["stat_reward"]
                self.last_toast = f"Boss down! +{self.result_info['xp_gain']} XP +{st_v} {st_k.upper()}"
            elif self.is_boss:
                self.last_toast = f"Boss down! +{self.result_info['xp_gain']} XP"
            else:
                self.last_toast = f"Won vs {self.rival['name']}! +{self.result_info['xp_gain']} XP"
        else:
            self.last_toast = f"Tough fight! +{self.result_info['xp_gain']} XP"

    def on_exit(self) -> None:
        save_pet(self.pet)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if self.phase == "choose":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return ("home", {"pet": self.pet, "return_toast": "Left the Arena."})
            if event.key in KEYS_LEFT:
                self.cmd_idx = (self.cmd_idx - 1) % len(COMMANDS)
            elif event.key in KEYS_RIGHT:
                self.cmd_idx = (self.cmd_idx + 1) % len(COMMANDS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                cmd_id = COMMANDS[self.cmd_idx][0]
                if cmd_id == "flee":
                    return ("home", {"pet": self.pet, "return_toast": "Escaped safely!"})
                if cmd_id == "skill" and self.player["sp"] < 2:
                    self.log_text = "Need 2 SP! Use Strike or Guard first."
                    return None
                self._queue_turn(cmd_id)

        elif self.phase == "result":
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                won = bool(self.result_info and self.result_info["won"])
                return (
                    "home",
                    {
                        "pet": self.pet,
                        "return_toast": self.last_toast,
                        "return_anim": "happy" if won else "idle",
                    },
                )
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ok, msg = self.pet.can_battle()
                if ok:
                    self._start_match()
                else:
                    return ("home", {"pet": self.pet, "return_toast": msg, "return_anim": "idle"})
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.player_anim.update(dt)
        self.rival_anim.update(dt)

        if self.p_lunge > 0:
            self.p_lunge = max(0.0, self.p_lunge - dt)
        if self.r_lunge > 0:
            self.r_lunge = max(0.0, self.r_lunge - dt)
        if self.p_shake > 0:
            self.p_shake = max(0.0, self.p_shake - dt)
        if self.r_shake > 0:
            self.r_shake = max(0.0, self.r_shake - dt)

        for p in self.popups:
            p["y"] -= 20.0 * dt
            p["life"] -= dt
        self.popups = [p for p in self.popups if p["life"] > 0]

        if self.phase == "executing":
            self.step_timer -= dt
            if self.step_timer <= 0:
                self._run_next_step()

    def _draw_fighter_hud(self, canvas: pygame.Surface, f: dict, x: int, y: int, w: int) -> None:
        boss_card = bool(f.get("is_boss"))
        rect = pygame.Rect(x, y, w, 28)
        pygame.draw.rect(canvas, BOSS_PANEL if boss_card else settings.COLOR_PANEL, rect, border_radius=4)
        pygame.draw.rect(canvas, BOSS_GOLD if boss_card else settings.COLOR_ACCENT, rect, 1, border_radius=4)

        if boss_card:
            draw_boss_crown(canvas, x + 4, y + 4)
            name_x = x + 15
            name_txt = f"{f['name'][:6]} L{f['level']}"
            name_col = BOSS_GOLD
        else:
            name_x = x + 5
            name_txt = f"{f['name'][:8]} L{f['level']}"
            name_col = settings.COLOR_TEXT

        name_s = self.fonts["sans"].render(name_txt, True, name_col)
        canvas.blit(name_s, (name_x, y + 2))

        hp_txt = f"{f['hp']}/{f['max_hp']}"
        hp_s = self.fonts["mono"].render(hp_txt, True, settings.COLOR_MUTED)
        canvas.blit(hp_s, (x + w - hp_s.get_width() - 5, y + 2))

        ratio = f["hp"] / max(1, f["max_hp"])
        col = HP_GOOD if ratio >= 0.5 else (HP_WARN if ratio >= 0.25 else HP_LOW)
        bar_x, bar_y, bar_w, bar_h = x + 5, y + 16, w - 42, 7
        pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h))
        if ratio > 0:
            pygame.draw.rect(canvas, col, (bar_x, bar_y, max(2, int(bar_w * ratio)), bar_h))
        pygame.draw.rect(canvas, BOSS_GOLD if boss_card else settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 1)

        for i in range(f["max_sp"]):
            px = x + w - 31 + i * 9
            py = y + 16
            pygame.draw.rect(canvas, SP_ON if i < f["sp"] else SP_OFF, (px, py, 6, 7), border_radius=1)

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill(BOSS_BG if self.is_boss else (22, 16, 40))

        # Twinkling arena sky (ember-gold stars during Boss challenges)
        for sx, sy, phase in self.stars:
            bright = math.sin(self.elapsed * 2.6 + phase) > 0.35
            if self.is_boss:
                col = BOSS_GOLD if bright else (122, 54, 88)
            else:
                col = (210, 200, 245) if bright else (90, 76, 134)
            canvas.fill(col, (sx, sy, 1, 1))

        # Arena floor & battle pads
        floor_col = (56, 26, 58) if self.is_boss else settings.COLOR_FLOOR
        line_col = BOSS_GOLD if self.is_boss else settings.COLOR_ACCENT
        pygame.draw.rect(canvas, floor_col, (0, 108, settings.LOGICAL_WIDTH, 18))
        pygame.draw.line(canvas, line_col, (0, 108), (settings.LOGICAL_WIDTH, 108), 1)
        pygame.draw.ellipse(canvas, (76, 52, 118), (30, 112, 76, 11))

        if self.is_boss:
            pygame.draw.ellipse(canvas, (118, 36, 62), (210, 111, 84, 13))
            pygame.draw.ellipse(canvas, BOSS_GOLD, (210, 111, 84, 13), 1)
        else:
            pygame.draw.ellipse(canvas, (76, 52, 118), (214, 112, 76, 11))

        # Top header
        pygame.draw.rect(canvas, BOSS_PANEL if self.is_boss else settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, line_col, (0, 22), (settings.LOGICAL_WIDTH, 22), 1)

        if self.is_boss:
            draw_boss_crown(canvas, 7, 7)
            canvas.blit(self.fonts["sans"].render("BOSS CHALLENGE", True, BOSS_GOLD), (20, 3))
            st_s = self.fonts["mono"].render(
                f"T{self.rival['boss_tier']} STRK:{self.pet.win_streak}", True, BOSS_CRIMSON
            )
        else:
            canvas.blit(self.fonts["sans"].render("BATTLE ARENA", True, SP_ON), (8, 3))
            st_s = self.fonts["mono"].render(
                f"STRK:{self.pet.win_streak}  W:{self.pet.battle_wins}", True, CYAN_COL
            )
        canvas.blit(st_s, (settings.LOGICAL_WIDTH - st_s.get_width() - 8, 3))

        # Fighter HP & SP cards
        self._draw_fighter_hud(canvas, self.player, 6, 26, 150)
        self._draw_fighter_hud(canvas, self.rival, 164, 26, 150)

        # Center Elite Boss tier badge in open mid-arena space
        if self.is_boss and self.phase != "result":
            badge_txt = f"ELITE {self.rival['boss_title']}"
            b_surf = self.fonts["mono"].render(badge_txt, True, BOSS_GOLD)
            bw = b_surf.get_width() + 14
            bx = (settings.LOGICAL_WIDTH - bw) // 2
            by = 58
            pygame.draw.rect(canvas, (76, 22, 46), (bx, by, bw, 16), border_radius=4)
            pygame.draw.rect(canvas, BOSS_GOLD, (bx, by, bw, 16), 1, border_radius=4)
            canvas.blit(b_surf, (bx + 7, by + 2))

        # Fighter sprites with lunge, shake, and pulsing Boss aura
        p_dx = int(14 * (self.p_lunge / 0.22)) + (random.randint(-3, 3) if self.p_shake > 0 else 0)
        r_dx = -int(14 * (self.r_lunge / 0.22)) + (random.randint(-3, 3) if self.r_shake > 0 else 0)

        if self.player["hp"] > 0:
            canvas.blit(self.player_anim.get_frame(), (36 + p_dx, 56))
        if self.rival["hp"] > 0:
            if self.is_boss:
                aura_r = 25 + int(math.sin(self.elapsed * 5.0) * 3)
                aura = pygame.Surface((68, 68), pygame.SRCALPHA)
                pygame.draw.circle(aura, (255, 198, 72, 36), (34, 34), aura_r)
                pygame.draw.circle(aura, (232, 72, 102, 54), (34, 34), max(8, aura_r - 7), 2)
                canvas.blit(aura, (218 + r_dx, 54))
            canvas.blit(self.rival_anim.get_frame(), (220 + r_dx, 56))

        # Floating damage / heal popups
        for p in self.popups:
            surf = self.fonts["mono"].render(p["text"], True, p["color"])
            canvas.blit(surf, (int(p["x"]), int(p["y"])))

        # Middle log / skill-preview strip
        pygame.draw.rect(canvas, (30, 20, 48), (0, 126, settings.LOGICAL_WIDTH, 20))
        pygame.draw.line(canvas, (72, 54, 108), (0, 126), (settings.LOGICAL_WIDTH, 126), 1)

        if self.phase == "choose" and COMMANDS[self.cmd_idx][0] == "skill":
            sp_tag = "2 SP" if self.player["sp"] >= 2 else "Need 2 SP"
            info_txt = f"{self.player['ability_name']} ({sp_tag})"
            info_col = SP_ON if self.player["sp"] >= 2 else HP_WARN
        else:
            info_txt = self.log_text
            info_col = BOSS_GOLD if (self.is_boss and self.phase == "choose") else settings.COLOR_TEXT

        log_s = self.fonts["sans"].render(info_txt, True, info_col)
        canvas.blit(log_s, ((settings.LOGICAL_WIDTH - log_s.get_width()) // 2, 129))

        # Victory / Defeat modal overlay
        if self.phase == "result" and self.result_info is not None:
            res = self.result_info
            boss_win = res["won"] and res.get("is_boss")
            card = pygame.Rect(18, 26, 284, 118)
            pygame.draw.rect(canvas, BOSS_PANEL if boss_win else settings.COLOR_PANEL, card, border_radius=6)
            border_col = BOSS_GOLD if res["won"] else HP_LOW
            pygame.draw.rect(canvas, border_col, card, 2, border_radius=6)

            if boss_win:
                head = "BOSS DEFEATED!"
            elif res["won"]:
                head = "VICTORY!"
            else:
                head = "DEFEATED"

            head_s = self.fonts["title"].render(head, True, border_col)
            hx = (settings.LOGICAL_WIDTH - head_s.get_width()) // 2
            canvas.blit(head_s, (hx, 31))
            if boss_win:
                draw_boss_crown(canvas, hx - 14, 38)
                draw_boss_crown(canvas, hx + head_s.get_width() + 5, 38)

            if res.get("leveled_up"):
                xp_line = f"LEVEL UP! Lv.{res['new_level']} (+{res['xp_gain']} XP)"
                xp_col = SP_ON
            else:
                xp_line = f"+{res['xp_gain']} XP   +{res['bond_gain']} Bond"
                xp_col = HP_GOOD
            xp_s = self.fonts["sans"].render(xp_line, True, xp_col)
            canvas.blit(xp_s, ((settings.LOGICAL_WIDTH - xp_s.get_width()) // 2, 60))

            if boss_win and res.get("stat_reward"):
                st_k, st_v = res["stat_reward"]
                bonus_s = self.fonts["mono"].render(f"BOSS BONUS: +{st_v} {st_k.upper()}!", True, BOSS_GOLD)
                canvas.blit(bonus_s, ((settings.LOGICAL_WIDTH - bonus_s.get_width()) // 2, 79))
                strk_y = 99
            else:
                strk_y = 84

            strk_s = self.fonts["mono"].render(
                f"Streak:{res['win_streak']}  Boss:{res['boss_wins']}  Wins:{res['battle_wins']}",
                True,
                CYAN_COL,
            )
            canvas.blit(strk_s, ((settings.LOGICAL_WIDTH - strk_s.get_width()) // 2, strk_y))

            if res["won"] and is_boss_fight(self.pet.win_streak):
                next_txt = f"NEXT: ELITE BOSS! (EN:{int(self.pet.energy)}%)"
                next_col = BOSS_GOLD if int(self.elapsed * 3) % 2 == 0 else BOSS_CRIMSON
            else:
                next_txt = f"Energy left: {int(self.pet.energy)}%"
                next_col = settings.COLOR_MUTED
            eng_s = self.fonts["sans"].render(next_txt, True, next_col)
            canvas.blit(eng_s, ((settings.LOGICAL_WIDTH - eng_s.get_width()) // 2, 120))

        # Bottom command bar (4 buttons or result prompt)
        dock_y = 146
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, dock_y, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, line_col, (0, dock_y), (settings.LOGICAL_WIDTH, dock_y), 1)

        if self.phase == "result":
            foot = self.fonts["sans"].render("Enter:Next Fight   Esc:Home", True, settings.COLOR_MUTED)
            canvas.blit(foot, ((settings.LOGICAL_WIDTH - foot.get_width()) // 2, 151))
            return

        btn_w, btn_h, gap = 74, 20, 4
        start_x = (settings.LOGICAL_WIDTH - (4 * btn_w + 3 * gap)) // 2
        for idx, (cmd_id, label) in enumerate(COMMANDS):
            bx = start_x + idx * (btn_w + gap)
            rect = pygame.Rect(bx, dock_y + 2, btn_w, btn_h)
            selected = self.phase == "choose" and idx == self.cmd_idx
            disabled = cmd_id == "skill" and self.player["sp"] < 2

            pygame.draw.rect(canvas, SEL_FILL if selected else SLOT_BG, rect, border_radius=4)
            pygame.draw.rect(
                canvas,
                BOSS_GOLD if (selected and self.is_boss) else (HP_GOOD if selected else SLOT_BORDER),
                rect,
                1,
                border_radius=4,
            )
            col = DISABLED_COL if disabled else (settings.COLOR_TEXT if selected else settings.COLOR_MUTED)
            lbl = self.fonts["sans"].render(label, True, col)
            canvas.blit(lbl, (bx + (btn_w - lbl.get_width()) // 2, dock_y + 4))