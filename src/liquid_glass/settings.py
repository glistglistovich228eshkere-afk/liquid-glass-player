"""User settings, stored in ~/.config/liquid-glass/settings.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .i18n import LANGUAGE_CHOICES
from .library import CONFIG_DIR

SETTINGS_FILE = CONFIG_DIR / "settings.json"

# theme key -> (display name key, stylesheet file)
THEMES = {
    "liquid-glass": ("theme_liquid_glass", "style.css"),
    "plain": ("theme_plain", "style-plain.css"),
}
THEME_ORDER = ["liquid-glass", "plain"]
DEFAULT_THEME = "liquid-glass"


@dataclass
class Settings:
    theme: str = DEFAULT_THEME
    username: str = ""
    display_name: str = ""
    avatar: str = ""
    language: str = "auto"


def _text(data: dict, key: str, limit: int) -> str:
    value = data.get(key)
    return value[:limit] if isinstance(value, str) else ""


def load_settings() -> Settings:
    try:
        data = json.loads(SETTINGS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return Settings()
    if not isinstance(data, dict):
        return Settings()
    theme = data.get("theme")
    language = data.get("language")
    return Settings(
        theme=theme if theme in THEMES else DEFAULT_THEME,
        username=_text(data, "username", 32),
        display_name=_text(data, "display_name", 64),
        avatar=_text(data, "avatar", 4096),
        language=language if language in LANGUAGE_CHOICES else "auto",
    )


def save_settings(settings: Settings) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), indent=2))
