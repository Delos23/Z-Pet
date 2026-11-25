"""Cross-platform display & input backend for Windows PC and Cardputer Zero (/dev/fb_lcd)."""

import os
from pathlib import Path
import struct
import sys
import pygame

import settings

# Linux EV_KEY codes -> Pygame keys (Cardputer Zero TCA8418 keyboard)
LINUX_KEYMAP = {
    1: pygame.K_ESCAPE,
    2: pygame.K_1, 3: pygame.K_2, 4: pygame.K_3, 5: pygame.K_4, 6: pygame.K_5,
    7: pygame.K_6, 8: pygame.K_7, 9: pygame.K_8, 10: pygame.K_9, 11: pygame.K_0,
    14: pygame.K_BACKSPACE,
    15: pygame.K_TAB,
    16: pygame.K_q, 17: pygame.K_w, 18: pygame.K_e, 19: pygame.K_r, 20: pygame.K_t,
    21: pygame.K_y, 22: pygame.K_u, 23: pygame.K_i, 24: pygame.K_o, 25: pygame.K_p,
    28: pygame.K_RETURN,
    30: pygame.K_a, 31: pygame.K_s, 32: pygame.K_d, 33: pygame.K_f, 34: pygame.K_g,
    35: pygame.K_h, 36: pygame.K_j, 37: pygame.K_k, 38: pygame.K_l,
    44: pygame.K_z, 45: pygame.K_x, 46: pygame.K_c, 47: pygame.K_v, 48: pygame.K_b,
    49: pygame.K_n, 50: pygame.K_m,
    57: pygame.K_SPACE,
    103: pygame.K_UP, 105: pygame.K_LEFT, 106: pygame.K_RIGHT, 108: pygame.K_DOWN,
}

EV_KEY = 1
INPUT_EVENT_FMT = "llHHi"
INPUT_EVENT_SIZE = struct.calcsize(INPUT_EVENT_FMT)
FBIOGET_VSCREENINFO = 0x4600


def _detect_fb_device() -> str | None:
    """Returns /dev/fb_lcd (or /dev/fb0) when running headless on the Cardputer Zero."""
    if not settings.IS_HANDHELD:
        return None
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return None
    for candidate in ("/dev/fb_lcd", "/dev/fb0"):
        if os.path.exists(candidate):
            return candidate
    return None


def prepare_environment() -> bool:
    """Call BEFORE pygame.init(). Returns True if direct /dev/fb_lcd mode will be used."""
    if _detect_fb_device() is not None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        return True
    return False


class DisplayBackend:
    """Handles presentation and keyboard input on both PC windows and Cardputer Zero."""

    def __init__(self, use_fb: bool = False):
        self.use_fb = use_fb
        self.window: pygame.Surface | None = None
        self.fb_fd: int | None = None
        self.fb_surf: pygame.Surface | None = None
        self.fb_size: tuple[int, int] = (settings.LOGICAL_WIDTH, settings.LOGICAL_HEIGHT)
        self.fb_stride: int = 0
        self.fb_row_bytes: int = 0
        self.input_fds: list[int] = []

        if self.use_fb:
            self._init_framebuffer()
            self._init_evdev_inputs()
        else:
            self._init_window()

    def _init_window(self) -> None:
        if "--fullscreen" in sys.argv:
            pygame.mouse.set_visible(False)
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            pygame.display.set_caption("Z-Pet (320x170 Preview)")
            self.window = pygame.display.set_mode(
                (settings.LOGICAL_WIDTH * settings.PC_SCALE, settings.LOGICAL_HEIGHT * settings.PC_SCALE)
            )

    def _init_framebuffer(self) -> None:
        import fcntl

        fb_path = _detect_fb_device() or "/dev/fb_lcd"
        # Dummy 1x1 mode lets Pygame's convert_alpha() work cleanly without kmsdrm
        pygame.display.set_mode((1, 1))

        self.fb_fd = os.open(fb_path, os.O_RDWR)

        # Query exact resolution, bit depth, and RGB bitmasks from the LCD driver
        vinfo = bytearray(160)
        fcntl.ioctl(self.fb_fd, FBIOGET_VSCREENINFO, vinfo)
        fields = struct.unpack("40I", vinfo)
        xres, yres = fields[0], fields[1]
        bpp = fields[6]
        r_off, r_len = fields[8], fields[9]
        g_off, g_len = fields[11], fields[12]
        b_off, b_len = fields[14], fields[15]

        r_mask = ((1 << r_len) - 1) << r_off
        g_mask = ((1 << g_len) - 1) << g_off
        b_mask = ((1 << b_len) - 1) << b_off

        self.fb_size = (xres, yres)
        self.fb_row_bytes = xres * (bpp // 8)

        # Read exact row stride from sysfs if available
        real_fb = Path(os.path.realpath(fb_path)).name
        stride_file = Path(f"/sys/class/graphics/{real_fb}/stride")
        if stride_file.exists():
            self.fb_stride = int(stride_file.read_text().strip())
        else:
            self.fb_stride = self.fb_row_bytes

        self.fb_surf = pygame.Surface((xres, yres), 0, bpp, (r_mask, g_mask, b_mask, 0))
        print(f"Z-Pet framebuffer ready: {fb_path} ({xres}x{yres} {bpp}bpp stride={self.fb_stride})", flush=True)

    def _init_evdev_inputs(self) -> None:
        for dev in sorted(Path("/dev/input").glob("event*")):
            try:
                fd = os.open(str(dev), os.O_RDONLY | os.O_NONBLOCK)
                self.input_fds.append(fd)
            except OSError:
                continue

    def poll_hardware_keys(self) -> None:
        """Reads physical Cardputer Zero keypresses and posts them as Pygame KEYDOWN events."""
        if not self.use_fb:
            return

        for fd in self.input_fds:
            while True:
                try:
                    data = os.read(fd, INPUT_EVENT_SIZE * 16)
                except BlockingIOError:
                    break
                except OSError:
                    break

                if not data:
                    break

                for offset in range(0, len(data) - INPUT_EVENT_SIZE + 1, INPUT_EVENT_SIZE):
                    _, _, ev_type, ev_code, ev_val = struct.unpack_from(INPUT_EVENT_FMT, data, offset)
                    if ev_type == EV_KEY and ev_val == 1:
                        pg_key = LINUX_KEYMAP.get(ev_code)
                        if pg_key is not None:
                            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pg_key))

    def present(self, canvas: pygame.Surface) -> None:
        """Pushes the 320x170 canvas to either the PC preview window or /dev/fb_lcd."""
        if not self.use_fb:
            assert self.window is not None
            if self.window.get_size() == canvas.get_size():
                self.window.blit(canvas, (0, 0))
            else:
                pygame.transform.scale(canvas, self.window.get_size(), self.window)
            pygame.display.flip()
            return

        assert self.fb_surf is not None and self.fb_fd is not None

        if self.fb_size == canvas.get_size():
            self.fb_surf.blit(canvas, (0, 0))
        elif self.fb_size == (canvas.get_height(), canvas.get_width()):
            rotated = pygame.transform.rotate(canvas, -90)
            self.fb_surf.blit(rotated, (0, 0))
        else:
            scaled = pygame.transform.scale(canvas, self.fb_size)
            self.fb_surf.blit(scaled, (0, 0))

        raw = bytes(self.fb_surf.get_buffer())
        if self.fb_stride == self.fb_row_bytes:
            os.pwrite(self.fb_fd, raw, 0)
        else:
            rows = []
            pad = b"\x00" * (self.fb_stride - self.fb_row_bytes)
            for y in range(self.fb_size[1]):
                start = y * self.fb_row_bytes
                rows.append(raw[start : start + self.fb_row_bytes] + pad)
            os.pwrite(self.fb_fd, b"".join(rows), 0)

    def close(self) -> None:
        if self.fb_fd is not None:
            try:
                os.close(self.fb_fd)
            except OSError:
                pass
            self.fb_fd = None

        for fd in self.input_fds:
            try:
                os.close(fd)
            except OSError:
                pass
        self.input_fds.clear()