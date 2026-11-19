"""User settings, stored in ~/.config/liquid-glass/settings.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .library import CONFIG_DIR

SETTINGS_FILE = CONFIG_DIR / "settings.json"

# theme key -> (label shown in settings, stylesheet file)
THEMES = {
    "liquid-glass": ("Liquid Glass", "style.css"),
    "plain": ("Plain dark", "style-plain.css"),
}
THEME_ORDER = ["liquid-glass", "plain"]
DEFAULT_THEME = "liquid-glass"


@dataclass
class Settings:
    theme: str = DEFAULT_THEME


def load_settings() -> Settings:
    try:
        data = json.loads(SETTINGS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return Settings()
    theme = data.get("theme") if isinstance(data, dict) else None
    return Settings(theme=theme if theme in THEMES else DEFAULT_THEME)


def save_settings(settings: Settings) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), indent=2))
