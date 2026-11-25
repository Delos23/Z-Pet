#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICON_SRC="$APP_DIR/assets/ui/z-pet-icon.png"
ICON_DST="/usr/share/APPLaunch/share/images/z-pet.png"
DESKTOP_DST="/usr/share/APPLaunch/applications/z-pet.desktop"

if [[ ! -f "$ICON_SRC" ]]; then
    echo "Icon not found at $ICON_SRC. Run 'python3 tools/generate_icon.py' first."
    exit 1
fi

chmod +x "$APP_DIR/deploy/run_zpet.sh"

echo "Installing Z-Pet icon to $ICON_DST..."
sudo install -Dm644 "$ICON_SRC" "$ICON_DST"

echo "Installing launcher symlink at /usr/bin/z-pet..."
sudo ln -sf "$APP_DIR/deploy/run_zpet.sh" /usr/bin/z-pet

echo "Registering Z-Pet with APPLaunch at $DESKTOP_DST..."
sudo tee "$DESKTOP_DST" >/dev/null <<'EOF'
[Desktop Entry]
Type=Application
Name=Z-Pet
Comment=Virtual pixel-art pet for Cardputer Zero
Exec=/usr/bin/z-pet
Icon=share/images/z-pet.png
Terminal=false
Categories=Game;
EOF

echo "Restarting APPLaunch..."
systemctl --user restart APPLaunch.service
echo "Done! Z-Pet is ready on your Cardputer Zero launcher."
