#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/.config/z-pet"
mkdir -p "$LOG_DIR"

# Use Linux DRM/KMS when launched without X11/Wayland (Cardputer Zero APPLaunch)
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    export SDL_VIDEODRIVER="kmsdrm"
fi

cd "$APP_DIR"
exec python3 main.py --fullscreen >>"$LOG_DIR/launch.log" 2>&1