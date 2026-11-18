"""Jamendo catalog search: free Creative Commons music that can be streamed directly.

Needs a free client ID from the Jamendo developer portal, supplied either as the
JAMENDO_CLIENT_ID environment variable or in ~/.config/liquid-glass/jamendo_client_id.

Jamendo matches names exactly, so each search is also run with individual words and
shortened long words, and the combined results are ranked by similarity to the query.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from .fuzzy import score, tokenize
from .library import CONFIG_DIR, Track

API_BASE = "https://api.jamendo.com/v3.0"
CLIENT_ID_FILE = CONFIG_DIR / "jamendo_client_id"
USER_AGENT = "liquid-glass-player/0.1"
MAX_REQUESTS = 6


class JamendoError(Exception):
    """Raised when a Jamendo request fails in a way the user should see."""


def load_client_id() -> str | None:
    env_value = os.environ.get("JAMENDO_CLIENT_ID", "").strip()
    if env_value:
        return env_value
    if CLIENT_ID_FILE.exists():
        return CLIENT_ID_FILE.read_text().strip() or None
    return None


def _request(name: str, client_id: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "format": "json",
            "limit": limit,
            "namesearch": name,
        }
    )
    request = urllib.request.Request(f"{API_BASE}/tracks/?{params}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except OSError as exc:
        raise JamendoError(f"network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise JamendoError("unexpected response from Jamendo") from exc

    header = payload.get("headers", {}) if isinstance(payload, dict) else {}
    if header.get("status") not in (None, "success"):
        raise JamendoError(header.get("error_message") or "Jamendo returned an error")
    return payload.get("results", [])


def _query_variants(query: str) -> list[str]:
    """Queries to send to Jamendo: the full text, then its words, then shortened long words."""
    words = tokenize(query)
    variants = [query.strip()]
    variants += [word for word in words if len(word) >= 3]
    variants += [word[:-2] for word in words if len(word) >= 6]

    unique: list[str] = []
    for variant in variants:
        if variant and variant not in unique:
            unique.append(variant)
    return unique[:MAX_REQUESTS]


def _to_track(item: dict) -> Track | None:
    stream_url = item.get("audio")
    if not stream_url:
        return None
    return Track(
        path=stream_url,
        title=item.get("name") or "Untitled",
        artist=item.get("artist_name") or "Unknown Artist",
        album=item.get("album_name") or "Unknown Album",
        number=0,
        art_url=item.get("album_image") or item.get("image") or "",
    )


def search_tracks(query: str, client_id: str, limit: int = 30) -> list[Track]:
    seen: set[str] = set()
    tracks: list[Track] = []

    for index, variant in enumerate(_query_variants(query)):
        try:
            items = _request(variant, client_id, limit)
        except JamendoError:
            if index == 0:
                raise  # the main search must succeed; extra variants are best effort
            continue
        for item in items:
            track = _to_track(item)
            if track is None or track.path in seen:
                continue
            seen.add(track.path)
            tracks.append(track)

    tracks.sort(key=lambda t: -score(query, f"{t.artist} {t.title} {t.album}"))
    return tracks


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read()
