"""Local music library: folder scanning, tag parsing, embedded artwork and saved online tracks."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import mutagen

AUDIO_EXTENSIONS = {".flac", ".mp3", ".ogg", ".oga", ".opus", ".wav"}

# Remembers the last chosen music folder between launches.
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "liquid-glass"
CONFIG_FILE = CONFIG_DIR / "folder"
# Tracks added from online sources (e.g. Jamendo) are saved here.
ONLINE_FILE = CONFIG_DIR / "online.json"


@dataclass(frozen=True)
class Track:
    path: str  # local file path, or an http(s) stream URL for online tracks
    title: str
    artist: str
    album: str
    number: int
    art_url: str = ""

    @property
    def is_remote(self) -> bool:
        return self.path.startswith(("http://", "https://"))

    @property
    def uri(self) -> str:
        if self.is_remote:
            return self.path
        return Path(self.path).as_uri()

    @property
    def haystack(self) -> str:
        return f"{self.artist} {self.album} {self.title}".lower()


def _first(tags, key: str, default: str = "") -> str:
    if not tags:
        return default
    values = tags.get(key)
    if not values:
        return default
    value = str(values[0]).strip()
    return value or default


def read_track(path: Path) -> Track:
    """Read basic tags. Falls back to the file name when tags are missing."""
    try:
        audio = mutagen.File(path, easy=True)
    except Exception:
        audio = None

    tags = getattr(audio, "tags", None)

    number = 0
    try:
        number = int(_first(tags, "tracknumber", "0").split("/")[0])
    except ValueError:
        number = 0

    return Track(
        path=str(path),
        title=_first(tags, "title", path.stem),
        artist=_first(tags, "artist", "Unknown Artist"),
        album=_first(tags, "album", "Unknown Album"),
        number=number,
    )


def scan(root: Path) -> list[Track]:
    """Recursively collect audio files under ``root``, sorted for album order."""
    root = root.expanduser().resolve()
    tracks: list[Track] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            file_path = Path(dirpath) / name
            if file_path.suffix.lower() in AUDIO_EXTENSIONS:
                tracks.append(read_track(file_path))
    tracks.sort(key=lambda t: (t.artist.lower(), t.album.lower(), t.number, t.title.lower()))
    return tracks


def extract_art(path: Path) -> bytes | None:
    """Return embedded cover art bytes for FLAC or MP3 files, if present."""
    try:
        audio = mutagen.File(path)
    except Exception:
        return None
    if audio is None:
        return None

    pictures = getattr(audio, "pictures", None)  # FLAC
    if pictures:
        return pictures[0].data

    tags = getattr(audio, "tags", None)  # ID3 (MP3)
    if tags is not None and hasattr(tags, "getall"):
        frames = tags.getall("APIC")
        if frames:
            return frames[0].data
    return None


def load_online() -> list[Track]:
    """Load online tracks previously added to the library."""
    try:
        items = json.loads(ONLINE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    known = {f.name for f in fields(Track)}
    tracks = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            tracks.append(Track(**{k: v for k, v in item.items() if k in known}))
    return tracks


def save_online(tracks: list[Track]) -> None:
    ONLINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ONLINE_FILE.write_text(json.dumps([asdict(t) for t in tracks], indent=2))
