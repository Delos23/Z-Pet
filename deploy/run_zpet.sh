#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
APP_DIR="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
LOG_DIR="$HOME/.config/z-pet"
mkdir -p "$LOG_DIR"

export PYGAME_HIDE_SUPPORT_PROMPT=1
unset DISPLAY WAYLAND_DISPLAY SDL_VIDEODRIVER SDL_AUDIODRIVER

# Expose PipeWire / PulseAudio sockets when launched from APPLaunch
if [ -z "${XDG_RUNTIME_DIR:-}" ]; then
    UID_NUM="$(id -u)"
    if [ -d "/run/user/$UID_NUM" ]; then
        export XDG_RUNTIME_DIR="/run/user/$UID_NUM"
    elif [ -d "/run/user/1000" ]; then
        export XDG_RUNTIME_DIR="/run/user/1000"
    fi
fi

if [ -n "${XDG_RUNTIME_DIR:-}" ]; then
    export PIPEWIRE_RUNTIME_DIR="$XDG_RUNTIME_DIR"
    if [ -S "$XDG_RUNTIME_DIR/pulse/native" ]; then
        export PULSE_SERVER="unix:$XDG_RUNTIME_DIR/pulse/native"
    fi
fi

cd "$APP_DIR"
exec python3 -u "$APP_DIR/main.py" >"$LOG_DIR/launch.log" 2>&1