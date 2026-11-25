from datetime import datetime
import math
import random
import sys
import pygame

import settings
from core.animator import load_species_animations
from core.pet import Pet
from core.save_manager import load_pet, save_pet

# Set to a number like 6.0 (Dawn), 12.0 (Noon), 18.5 (Sunset), or 22.0 (Night)
# to preview sky phases; leave as None to sync with your real clock / RTC.
CLOCK_OVERRIDE_HOUR: float | None = None

# Stat bar & room colors
BAR_BG = (52, 42, 74)
BAR_GOOD = (105, 225, 145)
BAR_WARN = (245, 195, 85)
BAR_LOW = (240, 95, 115)
HEART_COLOR = (255, 105, 165)

# Permanent pet bed placement in the right corner of the room
BED_X = 240
WALK_TO_BED_X = BED_X - 6  # Matches Sparkkit's x_off=-3 in sleep_start & wake_up


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


def get_clock_info() -> tuple[float, str]:
    """Returns (hour_as_float, '12-hour time') from real system time or debug override."""
    if CLOCK_OVERRIDE_HOUR is not None:
        hour_float = CLOCK_OVERRIDE_HOUR % 24.0
        hh = int(hour_float)
        mm = int((hour_float - hh) * 60)
    else:
        now = datetime.now()
        hh, mm = now.hour, now.minute
        hour_float = hh + mm / 60.0

    period = "AM" if hh < 12 else "PM"
    hour_12 = hh % 12 or 12
    return hour_float, f"{hour_12}:{mm:02d}{period}"


def load_bed_sprite(species_dir) -> pygame.Surface:
    bed_path = species_dir / "bed.png"
    img = pygame.image.load(str(bed_path)).convert_alpha()
    size = settings.SPRITE_SIZE * settings.SPRITE_SCALE
    return pygame.transform.scale(img, (size, size))


def load_poop_sprite() -> pygame.Surface:
    custom_path = settings.ASSETS_DIR / "ui" / "poop.png"
    if custom_path.exists():
        img = pygame.image.load(str(custom_path)).convert_alpha()
        return pygame.transform.scale(img, (16, 16))

    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    outline = (30, 18, 12, 255)
    brown = (128, 78, 42, 255)
    highlight = (166, 112, 68, 255)

    pygame.draw.rect(surf, outline, (2, 10, 12, 5))
    pygame.draw.rect(surf, brown, (3, 11, 10, 3))
    pygame.draw.rect(surf, outline, (4, 7, 8, 4))
    pygame.draw.rect(surf, brown, (5, 8, 6, 3))
    pygame.draw.rect(surf, highlight, (5, 8, 2, 1))
    pygame.draw.rect(surf, outline, (6, 4, 4, 4))
    pygame.draw.rect(surf, brown, (7, 5, 2, 3))
    pygame.draw.rect(surf, highlight, (7, 5, 1, 1))
    return surf


def draw_pixel_heart(surf: pygame.Surface, x: int, y: int, color: tuple = HEART_COLOR) -> None:
    pattern = [
        ".##.##.",
        "#######",
        "#######",
        ".#####.",
        "..###..",
        "...#...",
    ]
    for r, row in enumerate(pattern):
        for c, ch in enumerate(row):
            if ch == "#":
                surf.set_at((x + c, y + r), color)


def draw_clock_window(canvas: pygame.Surface, hour_float: float, elapsed: float) -> None:
    """Draws the bedroom window synced to the real clock (Dawn, Day, Sunset, Night)."""
    wx, wy, ww, wh = 18, 40, 44, 28
    win_rect = pygame.Rect(wx, wy, ww, wh)
    canvas.set_clip(win_rect)

    if 5.0 <= hour_float < 7.5:
        # Dawn: lavender sky + warm peach horizon + rising sun
        t = (hour_float - 5.0) / 2.5
        pygame.draw.rect(canvas, (76, 70, 138), (wx, wy, ww, 15))
        pygame.draw.rect(canvas, (238, 152, 128), (wx, wy + 15, ww, 13))
        sun_x = wx + 8 + int(t * 8)
        sun_y = wy + 24 - int(t * 10)
        pygame.draw.circle(canvas, (255, 214, 120), (sun_x, sun_y), 4)

    elif 7.5 <= hour_float < 17.5:
        # Daytime: bright sky + sun arcing smoothly across the window + drifting clouds
        t = (hour_float - 7.5) / 10.0
        pygame.draw.rect(canvas, (74, 144, 216), (wx, wy, ww, 17))
        pygame.draw.rect(canvas, (124, 186, 236), (wx, wy + 17, ww, 11))

        sun_x = wx + 6 + int(t * (ww - 12))
        sun_y = wy + 17 - int(math.sin(t * math.pi) * 10)
        pygame.draw.circle(canvas, (255, 232, 112), (sun_x, sun_y), 4)

        cloud_x = wx - 12 + int((elapsed * 3.5) % (ww + 16))
        pygame.draw.rect(canvas, (242, 246, 255), (cloud_x, wy + 16, 12, 4))
        pygame.draw.rect(canvas, (242, 246, 255), (cloud_x + 3, wy + 13, 6, 3))

    elif 17.5 <= hour_float < 20.0:
        # Sunset / Dusk: deep twilight top + orange-coral horizon + sinking sun
        t = (hour_float - 17.5) / 2.5
        pygame.draw.rect(canvas, (52, 38, 102), (wx, wy, ww, 14))
        pygame.draw.rect(canvas, (226, 108, 92), (wx, wy + 14, ww, 14))
        sun_x = wx + 28 + int(t * 8)
        sun_y = wy + 13 + int(t * 12)
        pygame.draw.circle(canvas, (255, 172, 92), (sun_x, sun_y), 4)
        if t > 0.45:
            canvas.fill((240, 240, 255), (wx + 9, wy + 6, 1, 1))

    else:
        # Night: midnight sky + crescent moon arc + twinkling stars
        night_h = (hour_float - 20.0) % 24.0
        t = min(1.0, night_h / 9.0)
        sky = (14, 18, 46)
        pygame.draw.rect(canvas, sky, win_rect)

        moon_x = wx + 7 + int(t * (ww - 14))
        moon_y = wy + 16 - int(math.sin(t * math.pi) * 8)
        pygame.draw.circle(canvas, (255, 242, 175), (moon_x, moon_y), 4)
        pygame.draw.circle(canvas, sky, (moon_x + 2, moon_y - 1), 3)

        twinkle = int(elapsed * 2) % 2 == 0
        s1 = (245, 245, 255) if twinkle else (140, 148, 200)
        s2 = (140, 148, 200) if twinkle else (245, 245, 255)
        canvas.fill(s1, (wx + 7, wy + 7, 2, 2))
        canvas.fill(s2, (wx + 24, wy + 19, 1, 1))
        canvas.fill(s1, (wx + 35, wy + 8, 1, 1))
        canvas.fill(s2, (wx + 13, wy + 21, 1, 1))

    canvas.set_clip(None)

    # Window frame & mullions
    frame_col = settings.COLOR_ACCENT
    pygame.draw.rect(canvas, frame_col, win_rect, 2)
    pygame.draw.line(canvas, frame_col, (wx + ww // 2, wy), (wx + ww // 2, wy + wh - 1), 1)
    pygame.draw.line(canvas, frame_col, (wx, wy + wh // 2), (wx + ww - 1, wy + wh // 2), 1)


def draw_thought_bubble(canvas: pygame.Surface, x: int, y: int, need: str) -> None:
    bx = max(6, min(settings.LOGICAL_WIDTH - 28, x))
    by = max(38, y)

    pygame.draw.rect(canvas, (245, 240, 255), (bx, by, 20, 15), border_radius=4)
    pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bx, by, 20, 15), 1, border_radius=4)
    pygame.draw.rect(canvas, (245, 240, 255), (bx + 4, by + 16, 3, 3))
    pygame.draw.rect(canvas, (245, 240, 255), (bx + 1, by + 20, 2, 2))

    if need == "hunger":
        pygame.draw.rect(canvas, (215, 85, 85), (bx + 5, by + 4, 8, 6))
        pygame.draw.rect(canvas, (240, 215, 195), (bx + 13, by + 6, 3, 2))
    elif need == "clean":
        pygame.draw.rect(canvas, (132, 82, 44), (bx + 6, by + 9, 8, 3))
        pygame.draw.rect(canvas, (132, 82, 44), (bx + 8, by + 6, 4, 3))
        pygame.draw.rect(canvas, (132, 82, 44), (bx + 9, by + 4, 2, 2))
    elif need == "energy":
        pygame.draw.circle(canvas, (110, 90, 200), (bx + 10, by + 7), 4)
        pygame.draw.circle(canvas, (245, 240, 255), (bx + 12, by + 6), 3)
    elif need == "happy":
        canvas.fill((70, 50, 110), (bx + 6, by + 5, 2, 2))
        canvas.fill((70, 50, 110), (bx + 12, by + 5, 2, 2))
        pygame.draw.rect(canvas, (70, 50, 110), (bx + 7, by + 10, 6, 1))


def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    hours, rem_mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {rem_mins}m"
    return f"{rem_mins}m"


def draw_stat_bar(
    canvas: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    label: str,
    value: float,
) -> None:
    lbl = font.render(label, True, settings.COLOR_MUTED)
    canvas.blit(lbl, (x, y))

    bar_x, bar_y, bar_w, bar_h = x + 22, y + 2, 50, 7
    pygame.draw.rect(canvas, BAR_BG, (bar_x, bar_y, bar_w, bar_h))

    if value >= 60:
        fill_color = BAR_GOOD
    elif value >= 30:
        fill_color = BAR_WARN
    else:
        fill_color = BAR_LOW

    fill_w = int((max(0.0, min(100.0, value)) / 100.0) * bar_w)
    if fill_w > 0:
        pygame.draw.rect(canvas, fill_color, (bar_x, bar_y, fill_w, bar_h))
    pygame.draw.rect(canvas, settings.COLOR_ACCENT, (bar_x, bar_y, bar_w, bar_h), 1)


def draw_hud(
    canvas: pygame.Surface,
    font: pygame.font.Font,
    pet: Pet,
    clock_str: str,
    toast_msg: str,
) -> None:
    # Top HUD panel
    pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 0, settings.LOGICAL_WIDTH, 34))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 34), (settings.LOGICAL_WIDTH, 34), 1)

    header = font.render(f"{pet.name}  AGE:{pet.age_hours}h  BND:{pet.bond}", True, settings.COLOR_TEXT)
    canvas.blit(header, (6, 3))

    if not pet.alive:
        status_txt, status_col = "FAINTED", BAR_LOW
    elif pet.sleeping:
        status_txt, status_col = "ZZZ", settings.COLOR_ACCENT
    elif len(pet.poops) > 0:
        status_txt, status_col = f"MESSx{len(pet.poops)}", BAR_WARN
    else:
        status_txt, status_col = "OK", BAR_GOOD

    right_surf = font.render(f"{clock_str} {status_txt}", True, status_col)
    canvas.blit(right_surf, (settings.LOGICAL_WIDTH - right_surf.get_width() - 6, 3))

    draw_stat_bar(canvas, font, 6, 18, "HGR", pet.hunger)
    draw_stat_bar(canvas, font, 84, 18, "HAP", pet.happy)
    draw_stat_bar(canvas, font, 162, 18, "ENG", pet.energy)
    draw_stat_bar(canvas, font, 240, 18, "CLN", pet.clean)

    # Floating toast banner
    if toast_msg:
        msg_surf = font.render(toast_msg, True, settings.COLOR_TEXT)
        box_w = msg_surf.get_width() + 14
        box_x = (settings.LOGICAL_WIDTH - box_w) // 2
        pygame.draw.rect(canvas, settings.COLOR_PANEL, (box_x, 38, box_w, 16), border_radius=3)
        pygame.draw.rect(canvas, settings.COLOR_ACCENT, (box_x, 38, box_w, 16), 1, border_radius=3)
        canvas.blit(msg_surf, (box_x + 7, 40))

    # Bottom controls bar
    pygame.draw.rect(canvas, settings.COLOR_PANEL, (0, 150, settings.LOGICAL_WIDTH, 20))
    pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 150), (settings.LOGICAL_WIDTH, 150), 1)
    if not pet.alive:
        ctrl_text = "[R] Hatch New Egg    [Esc] Quit"
    else:
        sleep_label = "[S]Wake" if pet.sleeping else "[S]leep"
        ctrl_text = f"[F]Meal [T]reat [P]lay [C]lean {sleep_label} [H]ug"

    ctrl_surf = font.render(ctrl_text, True, settings.COLOR_MUTED)
    canvas.blit(ctrl_surf, ((settings.LOGICAL_WIDTH - ctrl_surf.get_width()) // 2, 154))


def main() -> None:
    pygame.init()
    window = create_display()
    canvas = pygame.Surface((settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT))
    dim_overlay = pygame.Surface((settings.LOGICAL_WIDTH, 116), pygame.SRCALPHA)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 10, bold=True)

    pet, offline_seconds = load_pet()

    sprite_dir = settings.SPRITES_DIR / pet.species_id
    animator = load_species_animations(
        sprite_dir,
        frame_w=settings.SPRITE_SIZE,
        frame_h=settings.SPRITE_SIZE,
        scale=settings.SPRITE_SCALE,
    )
    bed_sprite = load_bed_sprite(sprite_dir)
    poop_sprite = load_poop_sprite()

    rendered_size = settings.SPRITE_SIZE * settings.SPRITE_SCALE  # 64px
    pet_y = 128 - rendered_size
    walk_speed = 38.0
    bed_walk_speed = 62.0
    wander_timer = 2.0

    # Smooth bedtime state machine: awake -> walking_to_bed -> tucking_in -> sleeping -> waking_up
    if pet.alive and pet.sleeping:
        bed_state = "sleeping"
        pet_x = float(WALK_TO_BED_X)
        target_x = pet_x
        lamp_dim = 1.0
        animator.facing_left = False
        animator.play("sleep", restart=True)
    else:
        bed_state = "awake"
        pet_x = 112.0
        target_x = pet_x
        lamp_dim = 0.0

    toast_msg = ""
    toast_timer = 0.0
    if offline_seconds >= 60:
        toast_msg = f"Welcome back! Away {format_duration(offline_seconds)}"
        toast_timer = 3.5

    autosave_timer = 0.0
    elapsed = 0.0
    hearts: list[dict] = []

    def show_toast(message: str, duration: float = 2.2) -> None:
        nonlocal toast_msg, toast_timer
        toast_msg = message
        toast_timer = duration

    def spawn_hearts(count: int = 3) -> None:
        for _ in range(count):
            hearts.append({
                "x": pet_x + random.uniform(14, 46),
                "y": pet_y + random.uniform(10, 22),
                "vy": random.uniform(16.0, 26.0),
                "life": random.uniform(0.9, 1.4),
            })

    running = True
    while running:
        dt = min(clock.tick(settings.FPS) / 1000.0, 0.1)
        elapsed += dt

        # --- 1. Handle Input ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_s:
                    ok, msg = pet.toggle_sleep()
                    if ok:
                        if pet.sleeping:
                            # Start smooth bedtime sequence
                            bed_state = "walking_to_bed"
                        else:
                            # Smoothly wake up (or cancel walk if not in bed yet)
                            if bed_state in ("tucking_in", "sleeping"):
                                bed_state = "waking_up"
                                animator.facing_left = False
                                animator.play("wake_up", restart=True, next_anim="idle")
                            else:
                                bed_state = "awake"
                                animator.play("idle", restart=True)
                        save_pet(pet)
                    show_toast(msg)
                elif event.key == pygame.K_r and not pet.alive:
                    pet = Pet()
                    bed_state = "awake"
                    pet_x = 112.0
                    target_x = 112.0
                    lamp_dim = 0.0
                    save_pet(pet)
                    animator.play("happy", restart=True)
                    show_toast("A new Sparkkit hatched!")
                elif event.key == pygame.K_c:
                    ok, msg = pet.clean_room()
                    if ok:
                        if bed_state == "awake":
                            animator.play("happy", restart=True)
                        save_pet(pet)
                    show_toast(msg)
                elif event.key in (pygame.K_f, pygame.K_t, pygame.K_p, pygame.K_h):
                    if bed_state == "waking_up":
                        show_toast("Hold on, waking up!")
                    elif event.key == pygame.K_f:
                        ok, msg = pet.feed()
                        if ok:
                            animator.facing_left = False
                            animator.play("eat", restart=True)
                            save_pet(pet)
                        show_toast(msg)
                    elif event.key == pygame.K_t:
                        ok, msg = pet.give_treat()
                        if ok:
                            animator.facing_left = False
                            animator.play("snack", restart=True)
                            spawn_hearts(2)
                            save_pet(pet)
                        show_toast(msg)
                    elif event.key == pygame.K_p:
                        ok, msg = pet.play()
                        if ok:
                            animator.facing_left = False
                            animator.play("play", restart=True)
                            save_pet(pet)
                        show_toast(msg)
                    elif event.key == pygame.K_h:
                        ok, msg = pet.hug()
                        if ok:
                            animator.play("happy", restart=True)
                            spawn_hearts(4)
                            save_pet(pet)
                        show_toast(msg)

        # --- 2. Update Pet Simulation & Particles ---
        pet.update(dt)
        autosave_timer += dt
        if autosave_timer >= 30.0:
            save_pet(pet)
            autosave_timer = 0.0

        if toast_timer > 0:
            toast_timer -= dt
            if toast_timer <= 0:
                toast_msg = ""

        for h in hearts:
            h["y"] -= h["vy"] * dt
            h["life"] -= dt
        hearts = [h for h in hearts if h["life"] > 0]

        # --- 3. Smooth Bedtime State Machine & Lamp Fade ---
        if not pet.alive:
            bed_state = "awake"
            animator.play("idle")
        elif bed_state == "walking_to_bed":
            dx = WALK_TO_BED_X - pet_x
            if abs(dx) > 2.0:
                direction = 1.0 if dx > 0 else -1.0
                pet_x += direction * bed_walk_speed * dt
                animator.facing_left = direction < 0
                animator.play("walk")
            else:
                pet_x = float(WALK_TO_BED_X)
                animator.facing_left = False
                bed_state = "tucking_in"
                animator.play("sleep_start", restart=True, next_anim="sleep")
        elif bed_state == "tucking_in":
            if animator.current_name == "sleep":
                bed_state = "sleeping"
        elif bed_state == "sleeping":
            animator.facing_left = False
            animator.play("sleep")
        elif bed_state == "waking_up":
            if animator.current_name == "idle":
                bed_state = "awake"
                pet_x = float(WALK_TO_BED_X)
                target_x = 120.0  # Trot happily back onto the center rug
                wander_timer = 2.5
        elif not animator.is_playing_oneshot:
            # Normal awake wandering (stays clear of the bed in the right corner)
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
                    target_x = float(random.randint(20, BED_X - rendered_size - 8))
                    wander_timer = random.uniform(2.0, 4.5)

        if pet.alive:
            animator.update(dt)

        # Smooth bedroom lamp dim/brighten (~0.6s fade instead of an abrupt cut)
        target_dim = 1.0 if bed_state in ("tucking_in", "sleeping") else 0.0
        if lamp_dim < target_dim:
            lamp_dim = min(target_dim, lamp_dim + dt * 1.6)
        elif lamp_dim > target_dim:
            lamp_dim = max(target_dim, lamp_dim - dt * 1.6)

        # --- 4. Render onto 320x170 Canvas ---
        hour_float, clock_str = get_clock_info()

        # Room walls, floor & center rug
        canvas.fill(settings.COLOR_BG)
        pygame.draw.rect(canvas, settings.COLOR_FLOOR, (0, 126, settings.LOGICAL_WIDTH, 24))
        pygame.draw.line(canvas, settings.COLOR_ACCENT, (0, 126), (settings.LOGICAL_WIDTH, 126), 1)
        pygame.draw.ellipse(canvas, (68, 48, 102), (76, 130, 124, 14))

        # Draw floor poops
        for px_pos in pet.poops:
            canvas.blit(poop_sprite, (px_pos, 114))

        # Draw pet + permanent bed (bed is baked into sleep_start / sleep / wake_up)
        in_bed_anim = bed_state in ("tucking_in", "sleeping", "waking_up")
        if in_bed_anim:
            pygame.draw.ellipse(canvas, (14, 10, 24), pygame.Rect(BED_X + 4, 123, 56, 8))
            canvas.blit(animator.get_frame(), (BED_X, int(pet_y)))
        else:
            pygame.draw.ellipse(canvas, (14, 10, 24), pygame.Rect(BED_X + 4, 123, 56, 8))
            canvas.blit(bed_sprite, (BED_X, int(pet_y)))
            pygame.draw.ellipse(canvas, (18, 12, 28), pygame.Rect(int(pet_x) + 14, 124, 36, 7))
            canvas.blit(animator.get_frame(), (int(pet_x), int(pet_y)))

        # Smooth indoor lamp dimming overlay (dims bedroom while keeping outdoor window crisp)
        if lamp_dim > 0.01:
            dim_overlay.fill((8, 4, 20, int(lamp_dim * 120)))
            canvas.blit(dim_overlay, (0, 34))

        # Real-time clock window stays bright on top of indoor dimness
        draw_clock_window(canvas, hour_float, elapsed)

        # Floating Zzz once settled asleep
        if pet.alive and bed_state == "sleeping":
            bob = int(math.sin(elapsed * 2.5) * 3)
            zzz = font.render("Zzz", True, settings.COLOR_ACCENT)
            canvas.blit(zzz, (BED_X + 44, int(pet_y) + 12 + bob))

        # Thought bubble when awake and a stat is low
        need = pet.get_need_bubble()
        if need and bed_state == "awake" and not animator.is_playing_oneshot:
            bubble_bob = int(math.sin(elapsed * 4.0) * 2)
            draw_thought_bubble(canvas, int(pet_x) + 44, int(pet_y) - 6 + bubble_bob, need)

        # Floating pixel hearts
        for h in hearts:
            draw_pixel_heart(canvas, int(h["x"]), int(h["y"]))

        # Top & bottom HUD bars on top
        draw_hud(canvas, font, pet, clock_str, toast_msg)

        if window.get_size() == canvas.get_size():
            window.blit(canvas, (0, 0))
        else:
            pygame.transform.scale(canvas, window.get_size(), window)

        pygame.display.flip()

    save_pet(pet)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()