"""Build an ARM64 .deb package for Z-Pet natively on Windows (or Linux) using only stdlib."""

from __future__ import annotations

import io
import json
import pathlib
import sys
import tarfile
import textwrap
import time

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO_DIR / "app-builder.json"
DIST_DIR = REPO_DIR / "dist"

INCLUDE_ITEMS = (
    "main.py",
    "settings.py",
    "app-builder.json",
    "README.md",
    "LICENSE",
    "core",
    "scenes",
    "data",
    "assets",
    "deploy",
)

EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git", ".vscode"}
EXCLUDE_FILES = {
    ".DS_Store",
    "save.json",
    "config.json",
    "guide.json",
    "launch.log",
    "build_deb.sh",
}
EXCLUDE_EXTS = {".pyc", ".pyo"}

DEPENDS = [
    "python3",
    "python3-pygame",
    "libsdl2-mixer-2.0-0",
    "fonts-dejavu-core",
    "wireplumber",
]


def _make_tar_dir(tar: tarfile.TarFile, arcpath: str, mtime: int, seen: set[str]) -> None:
    parts = arcpath.strip("/").split("/")
    cur = "."
    if cur not in seen:
        ti = tarfile.TarInfo(name="./")
        ti.type = tarfile.DIRTYPE
        ti.mode = 0o755
        ti.uid = 0
        ti.gid = 0
        ti.uname = "root"
        ti.gname = "root"
        ti.mtime = mtime
        tar.addfile(ti)
        seen.add(cur)

    for part in parts:
        if not part or part == ".":
            continue
        cur = f"{cur}/{part}"
        if cur not in seen:
            ti = tarfile.TarInfo(name=cur + "/")
            ti.type = tarfile.DIRTYPE
            ti.mode = 0o755
            ti.uid = 0
            ti.gid = 0
            ti.uname = "root"
            ti.gname = "root"
            ti.mtime = mtime
            tar.addfile(ti)
            seen.add(cur)


def _add_tar_bytes(
    tar: tarfile.TarFile,
    arcpath: str,
    payload: bytes,
    mode: int,
    mtime: int,
    seen: set[str],
) -> None:
    parent = "/".join(arcpath.strip("/").split("/")[:-1])
    _make_tar_dir(tar, parent, mtime, seen)
    ti = tarfile.TarInfo(name="./" + arcpath.lstrip("./"))
    ti.type = tarfile.REGTYPE
    ti.mode = mode
    ti.size = len(payload)
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "root"
    ti.mtime = mtime
    tar.addfile(ti, io.BytesIO(payload))


def _add_tar_symlink(
    tar: tarfile.TarFile,
    arcpath: str,
    target: str,
    mtime: int,
    seen: set[str],
) -> None:
    parent = "/".join(arcpath.strip("/").split("/")[:-1])
    _make_tar_dir(tar, parent, mtime, seen)
    ti = tarfile.TarInfo(name="./" + arcpath.lstrip("./"))
    ti.type = tarfile.SYMTYPE
    ti.linkname = target
    ti.mode = 0o777
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "root"
    ti.mtime = mtime
    tar.addfile(ti)


def _ar_member(name: str, data: bytes, mtime: int) -> bytes:
    header = (
        f"{name:<16}"
        f"{mtime:<12d}"
        f"{0:<6d}"
        f"{0:<6d}"
        f"{'100644':<8}"
        f"{len(data):<10d}"
        "`\n"
    ).encode("ascii")
    if len(header) != 60:
        raise ValueError(f"Invalid ar header length for {name}: {len(header)}")
    pad = b"\n" if (len(data) % 2 == 1) else b""
    return header + data + pad


def _build_control_text(
    pkg_name: str,
    deb_version: str,
    deb_arch: str,
    installed_kb: int,
    author_name: str,
    author_gh: str,
    homepage: str,
    summary: str,
    description: str,
) -> bytes:
    lines = [
        f"Package: {pkg_name}",
        f"Version: {deb_version}",
        "Section: games",
        "Priority: optional",
        f"Architecture: {deb_arch}",
        f"Installed-Size: {installed_kb}",
        f"Maintainer: {author_name} <{author_gh}@users.noreply.github.com>",
        f"Depends: {', '.join(DEPENDS)}",
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
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    deb_rev = sys.argv[1] if len(sys.argv) > 1 else "1"
    deb_arch = sys.argv[2] if len(sys.argv) > 2 else "arm64"

    if not MANIFEST.is_file():
        print(f"Error: {MANIFEST} not found.", file=sys.stderr)
        return 1

    meta = json.loads(MANIFEST.read_text(encoding="utf-8"))
    store = meta.get("store", {})
    author = store.get("author", {})

    app_name = str(meta.get("app_name", "Z-Pet"))
    pkg_name = str(meta.get("package_name", "z-pet"))
    version = str(meta.get("version", "1.0.0"))
    summary = str(store.get("summary", "Pocket pixel-art virtual pet RPG"))
    description = str(store.get("description", ""))
    icon_rel = str(store.get("icon", "assets/images/z_pet_icon.png"))
    homepage = str(store.get("source_repo", ""))
    author_name = str(author.get("display_name", "Aaron Bumbarger"))
    author_gh = str(author.get("github", "delos23"))

    for req in ("main.py", "data/species.json", "deploy/run_zpet.sh", icon_rel):
        if not (REPO_DIR / req).is_file():
            print(f"Error: required file missing: {req}", file=sys.stderr)
            return 1

    deb_version = f"{version}-{deb_rev}"
    install_root = f"opt/{pkg_name}"
    mtime = int(time.time())

    # 1. Build data.tar.gz
    data_buf = io.BytesIO()
    seen_dirs: set[str] = set()
    total_bytes = 0
    file_count = 0

    with tarfile.open(fileobj=data_buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        for item_name in INCLUDE_ITEMS:
            src = REPO_DIR / item_name
            if not src.exists():
                continue

            paths = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file())
            for path in paths:
                rel = path.relative_to(REPO_DIR)
                if any(part in EXCLUDE_DIRS for part in rel.parts):
                    continue
                if rel.name in EXCLUDE_FILES or rel.suffix.lower() in EXCLUDE_EXTS:
                    continue

                raw = path.read_bytes()
                # Convert Windows CRLF to LF for shell scripts and main.py
                if rel.suffix.lower() == ".sh" or rel.as_posix() == "main.py":
                    raw = raw.replace(b"\r\n", b"\n")

                is_exec = (rel.parts[0] == "deploy" and rel.suffix.lower() == ".sh") or rel.as_posix() == "main.py"
                mode = 0o755 if is_exec else 0o644
                arcpath = f"{install_root}/{rel.as_posix()}"
                _add_tar_bytes(tar, arcpath, raw, mode, mtime, seen_dirs)
                total_bytes += len(raw)
                file_count += 1

        # CLI symlink: /usr/bin/z-pet -> /opt/z-pet/deploy/run_zpet.sh
        _add_tar_symlink(tar, f"usr/bin/{pkg_name}", f"/{install_root}/deploy/run_zpet.sh", mtime, seen_dirs)

        # APPLaunch .desktop file
        desktop_text = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={app_name}\n"
            f"Comment={summary}\n"
            f"Exec=/{install_root}/deploy/run_zpet.sh\n"
            f"Icon=/{install_root}/{icon_rel}\n"
            "Terminal=false\n"
            "Categories=Game;\n"
            "StartupNotify=false\n"
        ).encode("utf-8")
        _add_tar_bytes(tar, f"usr/share/APPLaunch/applications/{pkg_name}.desktop", desktop_text, 0o644, mtime, seen_dirs)
        total_bytes += len(desktop_text)
        file_count += 1

    data_tar_gz = data_buf.getvalue()
    installed_kb = max(1, (total_bytes + 1023) // 1024)

    # 2. Build control.tar.gz
    control_bytes = _build_control_text(
        pkg_name=pkg_name,
        deb_version=deb_version,
        deb_arch=deb_arch,
        installed_kb=installed_kb,
        author_name=author_name,
        author_gh=author_gh,
        homepage=homepage,
        summary=summary,
        description=description,
    )
    control_buf = io.BytesIO()
    with tarfile.open(fileobj=control_buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        ctrl_seen: set[str] = set()
        _add_tar_bytes(tar, "control", control_bytes, 0o644, mtime, ctrl_seen)
    control_tar_gz = control_buf.getvalue()

    # 3. Assemble final .deb (ar archive)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    out_deb = DIST_DIR / f"{pkg_name}_{deb_version}_{deb_arch}.deb"
    deb_bytes = (
        b"!<arch>\n"
        + _ar_member("debian-binary", b"2.0\n", mtime)
        + _ar_member("control.tar.gz", control_tar_gz, mtime)
        + _ar_member("data.tar.gz", data_tar_gz, mtime)
    )
    out_deb.write_bytes(deb_bytes)

    print(f"Built: {out_deb}")
    print(f"Files: {file_count} | Installed-Size: {installed_kb} KiB | Archive: {len(deb_bytes) / 1024:.1f} KiB")
    print("\n--- DEBIAN/control ---")
    print(control_bytes.decode("utf-8").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())