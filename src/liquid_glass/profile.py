"""Local profile: username, display name and icon image. Stored only on this machine."""

from __future__ import annotations

import shutil
from pathlib import Path

import gi

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib  # noqa: E402

from .library import CONFIG_DIR  # noqa: E402

MAX_USERNAME = 32
MAX_DISPLAY_NAME = 64
AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def clean_username(text: str) -> str:
    """Usernames may contain letters, digits, dots, dashes and underscores only."""
    allowed = "".join(ch for ch in text.strip() if ch.isalnum() or ch in "_.-")
    return allowed[:MAX_USERNAME]


def clean_display_name(text: str) -> str:
    return text.strip()[:MAX_DISPLAY_NAME]


def remove_avatar() -> None:
    for old in CONFIG_DIR.glob("avatar.*"):
        old.unlink(missing_ok=True)


def import_avatar(source: Path) -> str:
    """Copy an image into the config folder and return its path."""
    suffix = source.suffix.lower()
    if suffix not in AVATAR_EXTENSIONS:
        raise ValueError("Choose a PNG, JPG or WebP image")
    remove_avatar()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    destination = CONFIG_DIR / f"avatar{suffix}"
    shutil.copyfile(source, destination)
    return str(destination)


def load_avatar_paintable(path: str):
    if not path or not Path(path).is_file():
        return None
    try:
        return Gdk.Texture.new_from_filename(path)
    except GLib.Error:
        return None
