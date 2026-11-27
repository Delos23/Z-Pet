#!/usr/bin/env bash
set -euo pipefail

# Build an ARM64 .deb package for Z-Pet from app-builder.json.
# Usage: ./deploy/build_deb.sh [debian_revision] [arch]
# Example: ./deploy/build_deb.sh 1 arm64

DEB_REV="${1:-1}"
DEB_ARCH="${2:-arm64}"

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
REPO_DIR="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
MANIFEST="$REPO_DIR/app-builder.json"
DIST_DIR="$REPO_DIR/dist"

if [ ! -f "$MANIFEST" ]; then
    echo "Error: $MANIFEST not found." >&2
    exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "Error: dpkg-deb not found. Run this script on the Cardputer Zero (or Debian/WSL)." >&2
    exit 1
fi

# Read package metadata safely from app-builder.json without needing jq
eval "$(
python3 - "$MANIFEST" <<'PY'
import json, shlex, sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)

store = data.get("store", {})
author = store.get("author", {})

fields = {
    "APP_NAME": data.get("app_name", "Z-Pet"),
    "PKG_NAME": data.get("package_name", "z-pet"),
    "VERSION": data.get("version", "1.0.0"),
    "SUMMARY": store.get("summary", "Pocket pixel-art virtual pet RPG"),
    "DESCRIPTION": store.get("description", ""),
    "ICON_REL": store.get("icon", "assets/images/z_pet_icon.png"),
    "HOMEPAGE": store.get("source_repo", ""),
    "AUTHOR_NAME": author.get("display_name", "Aaron Bumbarger"),
    "AUTHOR_GH": author.get("github", "delos23"),
}

for k, v in fields.items():
    print(f"{k}={shlex.quote(str(v))}")
PY
)"

DEB_VERSION="${VERSION}-${DEB_REV}"
OUT_DEB="${DIST_DIR}/${PKG_NAME}_${DEB_VERSION}_${DEB_ARCH}.deb"
INSTALL_ROOT="/opt/${PKG_NAME}"

# Verify critical assets and entrypoints exist before staging
for req in "main.py" "data/species.json" "deploy/run_zpet.sh" "$ICON_REL"; do
    if [ ! -f "$REPO_DIR/$req" ]; then
        echo "Error: required file missing: $req" >&2
        exit 1
    fi
done

STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

PKG_APP_DIR="$STAGE_DIR${INSTALL_ROOT}"
mkdir -p \
    "$STAGE_DIR/DEBIAN" \
    "$PKG_APP_DIR" \
    "$STAGE_DIR/usr/bin" \
    "$STAGE_DIR/usr/share/APPLaunch/applications" \
    "$STAGE_DIR/usr/share/APPLaunch/share/images"

# Copy runtime files while excluding dev environments, caches, and user saves
copy_tree() {
    local rel="$1"
    if [ ! -e "$REPO_DIR/$rel" ]; then
        return 0
    fi
    if command -v rsync >/dev/null 2>&1; then
        rsync -a \
            --exclude='.venv/' \
            --exclude='venv/' \
            --exclude='__pycache__/' \
            --exclude='*.pyc' \
            --exclude='*.pyo' \
            --exclude='.git/' \
            --exclude='.vscode/' \
            --exclude='.DS_Store' \
            --exclude='save.json' \
            --exclude='config.json' \
            --exclude='guide.json' \
            --exclude='launch.log' \
            --exclude='build_deb.sh' \
            "$REPO_DIR/$rel" "$PKG_APP_DIR/"
    else
        cp -a "$REPO_DIR/$rel" "$PKG_APP_DIR/"
    fi
}

for item in main.py settings.py app-builder.json README.md LICENSE core scenes data assets deploy; do
    copy_tree "$item"
done

# Belt-and-suspenders cleanup (covers cp fallback when rsync is absent)
find "$PKG_APP_DIR" -type d \( -name '.venv' -o -name 'venv' -o -name '__pycache__' -o -name '.git' -o -name '.vscode' \) -prune -exec rm -rf {} +
find "$PKG_APP_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '.DS_Store' -o -name 'save.json' -o -name 'config.json' -o -name 'guide.json' -o -name 'launch.log' \) -delete
rm -f "$PKG_APP_DIR/deploy/build_deb.sh"

# Strip any Windows CRLF endings from staged shell scripts
find "$PKG_APP_DIR/deploy" -type f -name '*.sh' -exec sed -i 's/\r$//' {} +

# Create CLI launcher wrapper (/usr/bin/z-pet -> /opt/z-pet/deploy/run_zpet.sh)
cat > "$STAGE_DIR/usr/bin/${PKG_NAME}" <<EOF
#!/usr/bin/env bash
exec "${INSTALL_ROOT}/deploy/run_zpet.sh" "\$@"
EOF

cp "$PKG_APP_DIR/${ICON_REL}" "$STAGE_DIR/usr/share/APPLaunch/share/images/${PKG_NAME}.png"
chmod 0644 "$STAGE_DIR/usr/share/APPLaunch/share/images/${PKG_NAME}.png"

# Create APPLaunch desktop launcher
cat > "$STAGE_DIR/usr/share/APPLaunch/applications/${PKG_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=${SUMMARY}
Path=${INSTALL_ROOT}
Exec=${INSTALL_ROOT}/deploy/run_zpet.sh
Icon=share/images/${PKG_NAME}.png
Terminal=false
Categories=Game;
StartupNotify=false
EOF

# Set clean Debian permissions
# Set clean Debian permissions
find "$STAGE_DIR" -type d -exec chmod 0755 {} +
find "$STAGE_DIR" -type f -exec chmod 0644 {} +
find "$PKG_APP_DIR/deploy" -type f -name '*.sh' -exec chmod 0755 {} +
chmod 0755 "$PKG_APP_DIR/main.py"
chmod 0755 "$STAGE_DIR/usr/bin/${PKG_NAME}"

# Calculate installed size in KiB (excluding DEBIAN/)
INSTALLED_KB="$(du -sk --exclude="$STAGE_DIR/DEBIAN" "$STAGE_DIR" | awk '{print $1}')"

# Generate DEBIAN/control with properly wrapped multi-line Description
python3 - "$STAGE_DIR/DEBIAN/control" "$PKG_NAME" "$DEB_VERSION" "$DEB_ARCH" "$INSTALLED_KB" \
    "$AUTHOR_NAME" "$AUTHOR_GH" "$HOMEPAGE" "$SUMMARY" "$DESCRIPTION" <<'PY'
import sys, textwrap

(
    out_path,
    pkg_name,
    deb_version,
    deb_arch,
    installed_kb,
    author_name,
    author_gh,
    homepage,
    summary,
    description,
) = sys.argv[1:]

depends = ", ".join([
    "python3",
    "python3-pygame",
    "libsdl2-mixer-2.0-0",
    "fonts-dejavu-core",
    "wireplumber",
])

lines = [
    f"Package: {pkg_name}",
    f"Version: {deb_version}",
    "Section: games",
    "Priority: optional",
    f"Architecture: {deb_arch}",
    f"Installed-Size: {installed_kb}",
    f"Maintainer: {author_name} <{author_gh}@users.noreply.github.com>",
    f"Depends: {depends}",
]

if homepage:
    lines.append(f"Homepage: {homepage}")

lines.append(f"Description: {summary}")
if description.strip():
    for para in description.strip().splitlines():
        para = para.strip()
        if not para:
            lines.append(" .")
        else:
            for wrapped in textwrap.wrap(para, width=76):
                lines.append(f" {wrapped}")

with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
PY

chmod 0755 "$STAGE_DIR/DEBIAN"
chmod 0644 "$STAGE_DIR/DEBIAN/control"

mkdir -p "$DIST_DIR"
rm -f "$OUT_DEB"

dpkg-deb --root-owner-group --build "$STAGE_DIR" "$OUT_DEB"

echo
echo "=== Built Package Info ==="
dpkg-deb --info "$OUT_DEB"

echo
echo "=== Hygiene Check ==="
if dpkg-deb --contents "$OUT_DEB" | grep -E '(\.venv|__pycache__|\.pyc|save\.json|config\.json)' >/dev/null; then
    echo "WARNING: Unwanted dev or user files detected in package!" >&2
    exit 1
else
    echo "OK: No .venv, __pycache__, or local save files found."
fi

echo "Output: $OUT_DEB ($(du -h "$OUT_DEB" | awk '{print $1}'))"