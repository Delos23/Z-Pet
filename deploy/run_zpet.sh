#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
APP_DIR="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
LOG_DIR="$HOME/.config/z-pet"
mkdir -p "$LOG_DIR"

export PYGAME_HIDE_SUPPORT_PROMPT=1
unset DISPLAY WAYLAND_DISPLAY SDL_VIDEODRIVER
cd "$APP_DIR"
exec python3 -u "$APP_DIR/main.py" >"$LOG_DIR/launch.log" 2>&1
