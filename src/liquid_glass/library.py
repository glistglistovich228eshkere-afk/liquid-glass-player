"""Local music library: folder scanning, tag parsing and embedded artwork."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import mutagen

AUDIO_EXTENSIONS = {".flac", ".mp3", ".ogg", ".oga", ".opus", ".wav"}

# Remembers the last chosen music folder between launches.
CONFIG_FILE = (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "liquid-glass"
    / "folder"
)


@dataclass(frozen=True)
class Track:
    path: str
    title: str
    artist: str
    album: str
    number: int

    @property
    def uri(self) -> str:
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
