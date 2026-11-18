"""Jamendo catalog search: free Creative Commons music that can be streamed directly.

Needs a free client ID from https://developer.jamendo.com, supplied either as the
JAMENDO_CLIENT_ID environment variable or in ~/.config/liquid-glass/jamendo_client_id.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from .library import CONFIG_DIR, Track

API_BASE = "https://api.jamendo.com/v3.0"
CLIENT_ID_FILE = CONFIG_DIR / "jamendo_client_id"
USER_AGENT = "liquid-glass-player/0.1"


class JamendoError(Exception):
    """Raised when a Jamendo request fails in a way the user should see."""


def load_client_id() -> str | None:
    env_value = os.environ.get("JAMENDO_CLIENT_ID", "").strip()
    if env_value:
        return env_value
    if CLIENT_ID_FILE.exists():
        return CLIENT_ID_FILE.read_text().strip() or None
    return None


def search_tracks(query: str, client_id: str, limit: int = 30) -> list[Track]:
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "format": "json",
            "limit": limit,
            "namesearch": query,
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

    tracks: list[Track] = []
    for item in payload.get("results", []):
        stream_url = item.get("audio")
        if not stream_url:
            continue
        tracks.append(
            Track(
                path=stream_url,
                title=item.get("name") or "Untitled",
                artist=item.get("artist_name") or "Unknown Artist",
                album=item.get("album_name") or "Unknown Album",
                number=0,
                art_url=item.get("album_image") or item.get("image") or "",
            )
        )
    return tracks


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read()
