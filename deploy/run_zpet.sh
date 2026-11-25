#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/.config/z-pet"
mkdir -p "$LOG_DIR"

unset DISPLAY WAYLAND_DISPLAY SDL_VIDEODRIVER
cd "$APP_DIR"
exec python3 -u main.py --fullscreen >"$LOG_DIR/launch.log" 2>&1
