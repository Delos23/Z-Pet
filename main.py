import random
import sys
import pygame

import settings
from core.animator import load_species_animations


def create_display() -> pygame.Surface:
    fullscreen = settings.IS_HANDHELD or ("--fullscreen" in sys.argv)
    if fullscreen:
        pygame.mouse.set_visible(False)
        return pygame.display.set_mode(
            (settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT),
            pygame.FULLSCREEN,
        )

    pygame.display.set_caption("Z-Pet (320x170 Preview)")
    return pygame.display.set_mode(
        (settings.LOGICAL_WIDTH * settings.PC_SCALE, settings.LOGICAL_HEIGHT * settings.PC_SCALE)
    )


def draw_room(canvas: pygame.Surface, font: pygame.font.Font, state_label: str, fps: float) -> None:
    canvas.fill(settings.COLOR_BG)

    # Room floor
    pygame.draw.rect(canvas, settings.COLOR_FLOOR, (0, 126, settings.LOGICAL_WIDTH, 24))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 126), (settings.LOGICAL_WIDTH, 126), 1)

    # Top HUD bar
    pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 20))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 20), (settings.LOGICAL_WIDTH, 20), 1)
    title = font.render(f"Z-PET | SPARKKIT [{state_label.upper()}]", True, settings.COLOR_TEXT)
    fps_txt = font.render(f"{int(fps)}FPS", True, settings.COLOR_MUTED)
    canvas.blit(title, (8, 4))
    canvas.blit(fps_txt, (settings.LOGICAL_WIDTH - fps_txt.get_width() - 8, 4))

    # Bottom control bar
    pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 150, settings.LOGICAL_WIDTH, 20))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 150), (settings.LOGICAL_WIDTH, 150), 1)
    controls = font.render("[F] Feed   [P] Play   [Esc] Quit", True, settings.COLOR_MUTED)
    canvas.blit(controls, (36, 154))


def main() -> None:
    pygame.init()
    window = create_display()
    canvas = pygame.Surface((settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 11, bold=True)

    # IMPORTANT: Load sprite sheets AFTER set_mode() so convert_alpha() works
    sprite_dir = settings.SPRITES_DIR / "spark_kit"
    animator = load_species_animations(
        sprite_dir,
        frame_w=settings.SPRITE_SIZE,
        frame_h=settings.SPRITE_SIZE,
        scale=settings.SPRITE_SCALE,
    )

    # Pet position & simple wandering AI
    rendered_size = settings.SPRITE_SIZE * settings.SPRITE_SCALE  # 64px
    pet_x = float((settings.LOGICAL_WIDTH - rendered_size) // 2)
    pet_y = 128 - rendered_size  # Feet resting neatly on the floor
    target_x = pet_x
    walk_speed = 36.0            # Pixels per second
    wander_timer = 2.0

    running = True
    while running:
        # Cap dt to 0.1s so dragging the window doesn't teleport the pet
        dt = min(clock.tick(settings.FPS) / 1000.0, 0.1)

        # --- 1. Handle Input ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_f:
                    animator.play("eat", restart=True)
                elif event.key == pygame.K_p:
                    animator.play("happy", restart=True)

        # --- 2. Update Pet Movement & Animation ---
        if not animator.is_playing_oneshot:
            dx = target_x - pet_x
            if abs(dx) > 2.0:
                direction = 1.0 if dx > 0 else -1.0
                pet_x += direction * walk_speed * dt
                animator.facing_left = direction < 0
                animator.play("walk")
            else:
                animator.play("idle")
                wander_timer -= dt
                if wander_timer <= 0:
                    target_x = float(random.randint(20, settings.LOGICAL_WIDTH - rendered_size - 20))
                    wander_timer = random.uniform(2.0, 4.5)

        animator.update(dt)

        # --- 3. Render onto 320x170 Canvas, then Scale to Window ---
        draw_room(canvas, font, animator.current_name, clock.get_fps())

        # Soft elliptical shadow under Sparkkit
        shadow_rect = pygame.Rect(int(pet_x) + 14, 124, 36, 7)
        pygame.draw.ellipse(canvas, (18, 12, 28), shadow_rect)

        canvas.blit(animator.get_frame(), (int(pet_x), int(pet_y)))

        if window.get_size() == canvas.get_size():
            window.blit(canvas, (0, 0))
        else:
            pygame.transform.scale(canvas, window.get_size(), window)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()