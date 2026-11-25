"""Animated Evolution Ceremony scene for Z-Pet (320x170)."""

import math
import random
import pygame

import settings
from core.animator import load_species_animations
from core.pet import Pet
from core.save_manager import save_pet

GOLD_COL = (255, 224, 96)
GOOD_COL = (105, 225, 145)
SPARK_COL = (210, 175, 255)


class EvolveScene:
    """3-stage evolution ceremony: charge -> flash -> reveal."""

    accepts_text_input = False

    def __init__(self, fonts: dict, config: dict, pet: Pet, target_species_id: str):
        self.fonts = fonts
        self.config = config
        self.pet = pet
        self.target_species_id = target_species_id

        self.old_anim = load_species_animations(
            settings.SPRITES_DIR / pet.species_id,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=pet.color,
        )
        self.new_anim = load_species_animations(
            settings.SPRITES_DIR / target_species_id,
            frame_w=settings.SPRITE_SIZE,
            frame_h=settings.SPRITE_SIZE,
            scale=settings.SPRITE_SCALE,
            color_id=pet.color,
        )
        self.old_anim.play("idle", restart=True)
        self.new_anim.play("happy", restart=True, next_anim="idle")

        self.phase = "charge"  # charge -> flash -> reveal
        self.timer = 0.0
        self.evolve_info: dict | None = None
        self.flash_surf = pygame.Surface((settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT), pygame.SRCALPHA)

        rng = random.Random(77)
        self.orbs = [
            {"angle": rng.uniform(0, 6.28), "dist": rng.uniform(36, 78), "speed": rng.uniform(2.5, 4.5)}
            for _ in range(18)
        ]

    def _complete_evolution(self) -> None:
        if self.evolve_info is None:
            self.evolve_info = self.pet.evolve(self.target_species_id)
            save_pet(self.pet)
            self.new_anim.play("happy", restart=True, next_anim="idle")

    def handle_event(self, event: pygame.event.Event) -> tuple[str, dict] | None:
        if event.type != pygame.KEYDOWN:
            return None

        if self.phase == "reveal" and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            new_sp_name = self.evolve_info["new_species_name"] if self.evolve_info else "Adult"
            return (
                "home",
                {
                    "pet": self.pet,
                    "return_toast": f"{self.pet.name} evolved into {new_sp_name}!",
                    "return_anim": "happy",
                },
            )
        return None

    def update(self, dt: float) -> None:
        self.timer += dt
        self.old_anim.update(dt)
        self.new_anim.update(dt)

        if self.phase == "charge":
            for orb in self.orbs:
                orb["angle"] += orb["speed"] * dt
                orb["dist"] = max(6.0, orb["dist"] - 22.0 * dt)
            if self.timer >= 2.4:
                self.phase = "flash"
                self.timer = 0.0
                self._complete_evolution()

        elif self.phase == "flash":
            if self.timer >= 0.55:
                self.phase = "reveal"
                self.timer = 0.0

    def render(self, canvas: pygame.Surface) -> None:
        canvas.fill((18, 12, 34))

        if self.phase in ("charge", "flash"):
            cx, cy = settings.LOGICAL_WIDTH // 2, 82

            # Expanding energy aura rings
            pulse = 22 + int(math.sin(self.timer * 10.0) * 6)
            pygame.draw.circle(canvas, (76, 48, 134), (cx, cy), pulse + 12, 2)
            pygame.draw.circle(canvas, SPARK_COL, (cx, cy), pulse, 1)

            # Swirling energy orbs converging inward
            for idx, orb in enumerate(self.orbs):
                ox = int(cx + math.cos(orb["angle"]) * orb["dist"])
                oy = int(cy + math.sin(orb["angle"]) * orb["dist"] * 0.65)
                col = GOLD_COL if idx % 2 == 0 else SPARK_COL
                pygame.draw.rect(canvas, col, (ox - 1, oy - 1, 3, 3))

            # Accelerating flicker between baby and adult form
            if self.phase == "charge":
                freq = 6.0 + self.timer * 10.0
                show_new = int(self.timer * freq) % 2 == 1 and self.timer > 0.7
                frame = self.new_anim.get_frame() if show_new else self.old_anim.get_frame()
            else:
                frame = self.new_anim.get_frame()

            canvas.blit(frame, (cx - 32, cy - 32))

            msg = self.fonts["sans"].render(f"What? {self.pet.name} is evolving!", True, GOLD_COL)
            canvas.blit(msg, ((settings.LOGICAL_WIDTH - msg.get_width()) // 2, 134))

            if self.phase == "flash":
                alpha = int(max(0.0, 1.0 - (self.timer / 0.55)) * 255)
                self.flash_surf.fill((250, 242, 255, alpha))
                canvas.blit(self.flash_surf, (0, 0))
            return

        # --- Reveal Card ---
        info = self.evolve_info
        assert info is not None

        card = pygame.Rect(12, 10, 296, 130)
        pygame.draw.rect(canvas, settings.COLOR_PANEL, card, border_radius=6)
        pygame.draw.rect(canvas, GOLD_COL, card, 2, border_radius=6)

        care_tag = info.get("care_label", "RADIANT").upper()
        banner = self.fonts["title"].render(f"{care_tag} EVOLVE!", True, GOLD_COL)
        canvas.blit(banner, ((settings.LOGICAL_WIDTH - banner.get_width()) // 2, 15))
        pygame.draw.line(canvas, (82, 62, 122), (24, 41), (296, 41), 1)

        # Newly evolved adult sprite on left
        pygame.draw.ellipse(canvas, (18, 12, 30), pygame.Rect(28, 110, 48, 8))
        canvas.blit(self.new_anim.get_frame(), (20, 52))

        # Evolution details on right
        form_s = self.fonts["sans"].render(
            f"{self.pet.name} -> {info['new_species_name']}!",
            True,
            settings.COLOR_TEXT,
        )
        canvas.blit(form_s, (94, 48))

        sb = info["stat_bonus"]
        bonus_s = self.fonts["mono"].render(
            f"A+{sb['atk']} D+{sb['def']} S+{sb['spd']} I+{sb['int']}",
            True,
            GOOD_COL,
        )
        canvas.blit(bonus_s, (94, 68))

        ab_head = self.fonts["sans"].render(
            f"Skill: {info['ability_name']}",
            True,
            GOLD_COL,
        )
        canvas.blit(ab_head, (94, 90))

        ab_desc = self.fonts["sans"].render(info["ability_desc"], True, settings.COLOR_MUTED)
        canvas.blit(ab_desc, (94, 108))

        pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 148, settings.LOGICAL_WIDTH, 22))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 148), (settings.LOGICAL_WIDTH, 148), 1)
        foot = self.fonts["sans"].render("Press Enter / Space to Continue!", True, GOOD_COL)
        canvas.blit(foot, ((settings.LOGICAL_WIDTH - foot.get_width()) // 2, 152))