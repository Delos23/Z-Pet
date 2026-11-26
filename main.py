"""Z-Pet entry point and scene manager."""

import os
import signal
import sys
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import settings
from core.display import DisplayBackend, load_ui_font, prepare_environment
from core.save_manager import load_config
from core import sound
from scenes.evolve import EvolveScene
from scenes.home import HomeScene
from scenes.menu import NewPetScene, SettingsScene, TitleScene
from scenes.minigame import StarCatchScene
from scenes.status import StatusScene
from scenes.teach import TeachScene
from scenes.guide import GuideScene
from scenes.battle import BattleScene

def save_screenshot(canvas: pygame.Surface) -> str:
    """Saves an exact 320x170 PNG screenshot for CardputerZero Store submission."""
    dev_dir = settings.ASSETS_DIR / "images"
    try:
        dev_dir.mkdir(parents=True, exist_ok=True)
        probe = dev_dir / ".write_test"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        target_dir = dev_dir
    except OSError:
        target_dir = settings.SAVE_DIR / "screenshots"
        target_dir.mkdir(parents=True, exist_ok=True)

    idx = 1
    while (target_dir / f"screenshot{idx:02d}.png").exists():
        idx += 1
    out_file = target_dir / f"screenshot{idx:02d}.png"
    pygame.image.save(canvas, str(out_file))
    return out_file.name


def main() -> None:
    boot_start = time.monotonic()

    use_fb = prepare_environment()
    pygame.display.init()
    pygame.font.init()

    display = DisplayBackend(use_fb=use_fb)
    canvas = pygame.Surface((settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT))
    clock = pygame.time.Clock()

    fonts = {
        "sans": load_ui_font(12, mono=False),
        "mono": load_ui_font(12, mono=True),
        "title": load_ui_font(20, mono=False),
    }

    config = load_config()
    scene = TitleScene(fonts, config)
    sound.init(enabled=config.get("sound", True))
    running = True

    def switch_scene(next_name: str, payload: dict) -> None:
        nonlocal scene, running
        if hasattr(scene, "on_exit"):
            scene.on_exit()

        if next_name == "quit":
            running = False
        elif next_name == "title":
            scene = TitleScene(fonts, config)
        elif next_name == "new_pet":
            scene = NewPetScene(fonts, config)
        elif next_name == "settings":
            scene = SettingsScene(fonts, config)
        elif next_name == "home":
            scene = HomeScene(
                fonts,
                config,
                pet=payload["pet"],
                offline_seconds=payload.get("offline", 0.0),
                is_new=payload.get("is_new", False),
                return_toast=payload.get("return_toast", ""),
                return_anim=payload.get("return_anim"),
            )
        elif next_name == "teach":
            scene = TeachScene(fonts, config, pet=payload["pet"])
        elif next_name == "minigame":
            scene = StarCatchScene(fonts, config, pet=payload["pet"])
        elif next_name == "status":
            scene = StatusScene(fonts, config, pet=payload["pet"])
        elif next_name == "evolve":
            scene = EvolveScene(
                fonts,
                config,
                pet=payload["pet"],
                target_species_id=payload["target_species"],
            )
        
        elif next_name == "battle":
         scene = BattleScene(fonts, config, pet=payload["pet"])
        
        elif next_name == "guide":
             scene = GuideScene(
             fonts,
             config,
             return_to=payload.get("return_to", "title"),
             pet=payload.get("pet"),
         )        
         

    def handle_exit_signal(_signum, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, handle_exit_signal)
    signal.signal(signal.SIGINT, handle_exit_signal)

    print(f"Z-Pet ready in {time.monotonic() - boot_start:.2f}s (fb={use_fb})", flush=True)

    try:
        while running:
            dt = min(clock.tick(settings.FPS) / 1000.0, 0.1)
            display.poll_hardware_keys()

            capture_requested = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F12 or (
                        event.key == pygame.K_0 and not scene.accepts_text_input
                    ):
                        capture_requested = True
                        continue

                transition = scene.handle_event(event)
                if transition is not None:
                    switch_scene(*transition)
                    break

            if not running:
                break

            auto_transition = scene.update(dt)
            if auto_transition is not None:
                switch_scene(*auto_transition)
                if not running:
                    break

            scene.render(canvas)

            if capture_requested:
                saved_name = save_screenshot(canvas)
                if hasattr(scene, "show_toast"):
                    scene.show_toast(f"Saved {saved_name}!", duration=1.8)

            display.present(canvas)
    finally:
        if hasattr(scene, "on_exit"):
            scene.on_exit()
        display.close()
        pygame.font.quit()
        pygame.display.quit()

    sys.exit()


if __name__ == "__main__":
    main()