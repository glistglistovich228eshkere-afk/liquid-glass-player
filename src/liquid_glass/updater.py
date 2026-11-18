"""Checks GitHub for newer releases and launches the updater in a terminal."""

from __future__ import annotations

import re
import shutil
import subprocess
import urllib.request

from . import __version__

RAW_INIT_URL = (
    "https://raw.githubusercontent.com/glistglistovich228eshkere-afk/"
    "liquid-glass-player/main/src/liquid_glass/__init__.py"
)
UPDATE_COMMAND = "liquid-glass-update"
VERSION_PATTERN = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)
# (terminal program, flag placed before the command; None if the program takes the command directly)
TERMINALS = [("konsole", "-e"), ("gnome-terminal", "--"), ("kitty", None), ("alacritty", "-e"), ("xterm", "-e")]


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split(".") if part.isdigit())


def latest_version(timeout: float = 10) -> str | None:
    try:
        with urllib.request.urlopen(RAW_INIT_URL, timeout=timeout) as response:
            text = response.read().decode("utf-8", "replace")
    except OSError:
        return None
    match = VERSION_PATTERN.search(text)
    return match.group(1) if match else None


def newer_version_available() -> str | None:
    latest = latest_version()
    if latest and parse_version(latest) > parse_version(__version__):
        return latest
    return None


def launch_update() -> bool:
    """Run the update command in a terminal window. Returns False if no terminal was found."""
    for program, flag in TERMINALS:
        if shutil.which(program) is None:
            continue
        args = [program, flag, UPDATE_COMMAND] if flag else [program, UPDATE_COMMAND]
        subprocess.Popen(args)
        return True
    return False
