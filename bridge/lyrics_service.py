import re
from typing import Any

import requests


LRCLIB_URL = "https://lrclib.net/api/get"

REQUEST_HEADERS = {
    "User-Agent": (
        "DeskSync/0.1 "
        "ESP32-Spotify-Mini-Controller"
    )
}

TIMESTAMP_PATTERN = re.compile(
    r"\[(\d{1,2}):(\d{2}(?:\.\d{1,3})?)\]"
)

lyrics_cache: dict[str, dict[str, Any]] = {}


def parse_synced_lyrics(
    synced_lyrics: str | None,
) -> list[dict[str, Any]]:
    if not synced_lyrics:
        return []

    parsed_lines: list[dict[str, Any]] = []

    for raw_line in synced_lyrics.splitlines():
        timestamp_matches = list(
            TIMESTAMP_PATTERN.finditer(raw_line)
        )

        if not timestamp_matches:
            continue

        lyric_text = raw_line[
            timestamp_matches[-1].end():
        ].strip()

        for match in timestamp_matches:
            minutes = int(match.group(1))
            seconds = float(match.group(2))

            timestamp_ms = int(
                ((minutes * 60) + seconds) * 1000
            )

            parsed_lines.append({
                "time_ms": timestamp_ms,
                "text": lyric_text,
            })

    parsed_lines.sort(
        key=lambda line: line["time_ms"]
    )

    return parsed_lines


def parse_plain_lyrics(
    plain_lyrics: str | None,
) -> list[str]:
    if not plain_lyrics:
        return []

    return [
        line.strip()
        for line in plain_lyrics.splitlines()
        if line.strip()
    ]


def fetch_lyrics(
    title: str,
    artist: str,
    album: str,
    duration_ms: int,
) -> dict[str, Any]:
    duration_seconds = round(duration_ms / 1000)

    cache_key = (
        f"{title.lower()}|"
        f"{artist.lower()}|"
        f"{album.lower()}|"
        f"{duration_seconds}"
    )

    cached_result = lyrics_cache.get(cache_key)

    if cached_result is not None:
        return cached_result

    request_parameters = {
        "track_name": title,
        "artist_name": artist,
        "album_name": album,
        "duration": duration_seconds,
    }

    try:
        response = requests.get(
            LRCLIB_URL,
            params=request_parameters,
            headers=REQUEST_HEADERS,
            timeout=10,
        )

        if response.status_code == 404:
            result = {
                "available": False,
                "instrumental": False,
                "synced_lines": [],
                "plain_lines": [],
                "error": "Lyrics were not found.",
            }

            lyrics_cache[cache_key] = result
            return result

        response.raise_for_status()

        data = response.json()

        result = {
            "available": True,
            "instrumental": bool(
                data.get("instrumental")
            ),
            "synced_lines": parse_synced_lyrics(
                data.get("syncedLyrics")
            ),
            "plain_lines": parse_plain_lyrics(
                data.get("plainLyrics")
            ),
            "error": None,
        }

        lyrics_cache[cache_key] = result

        return result

    except requests.RequestException as error:
        return {
            "available": False,
            "instrumental": False,
            "synced_lines": [],
            "plain_lines": [],
            "error": f"Lyrics service error: {error}",
        }


def get_synced_window(
    lines: list[dict[str, Any]],
    progress_ms: int,
    requested_index: int | None,
) -> dict[str, Any]:
    if not lines:
        return empty_window()

    if requested_index is None:
        current_index = 0

        for index, line in enumerate(lines):
            if line["time_ms"] <= progress_ms:
                current_index = index
            else:
                break
    else:
        current_index = max(
            0,
            min(requested_index, len(lines) - 1),
        )

    return {
        "index": current_index,
        "line_count": len(lines),
        "previous": (
            lines[current_index - 1]["text"]
            if current_index > 0
            else ""
        ),
        "current": lines[current_index]["text"],
        "next": (
            lines[current_index + 1]["text"]
            if current_index < len(lines) - 1
            else ""
        ),
        "time_ms": lines[current_index]["time_ms"],
    }


def get_plain_window(
    lines: list[str],
    requested_index: int | None,
) -> dict[str, Any]:
    if not lines:
        return empty_window()

    current_index = requested_index or 0

    current_index = max(
        0,
        min(current_index, len(lines) - 1),
    )

    return {
        "index": current_index,
        "line_count": len(lines),
        "previous": (
            lines[current_index - 1]
            if current_index > 0
            else ""
        ),
        "current": lines[current_index],
        "next": (
            lines[current_index + 1]
            if current_index < len(lines) - 1
            else ""
        ),
    }


def empty_window() -> dict[str, Any]:
    return {
        "index": 0,
        "line_count": 0,
        "previous": "",
        "current": "",
        "next": "",
    }