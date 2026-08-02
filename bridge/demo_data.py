from datetime import datetime
from typing import Any


def demo_song() -> dict[str, Any]:
    return {
        "status": "online",
        "playing": True,
        "title": "DeskSync Demo Song",
        "artist": "Demo Artist",
        "album": "ESP32 Preview",
        "progress": 74000,
        "duration": 215000,
        "volume": 65,
        "device": "DeskSync Demo",
    }


def demo_system() -> dict[str, Any]:
    return {
        "cpu": {
            "percent": 24.5,
            "physical_cores": 6,
            "logical_cores": 12,
        },
        "memory": {
            "percent": 58.2,
            "used_gb": 9.3,
            "available_gb": 6.7,
            "total_gb": 16.0,
        },
        "disk": {
            "drive": "C:\\",
            "percent": 47.3,
            "used_gb": 238.4,
            "free_gb": 265.6,
            "total_gb": 504.0,
        },
        "network": {
            "sent_mb": 348.5,
            "received_mb": 1254.8,
        },
        "battery": {
            "percent": 82,
            "charging": False,
        },
        "uptime": {
            "seconds": 9234,
            "readable": "2h 33m",
        },
    }


def demo_lyrics() -> dict[str, Any]:
    return {
        "status": "online",
        "title": "DeskSync Demo Song",
        "artist": "Demo Artist",
        "album": "ESP32 Preview",
        "playing": True,
        "progress_ms": 74000,
        "duration_ms": 215000,
        "instrumental": False,
        "lyrics_type": "synced",
        "mode": "automatic",
        "lyrics": {
            "previous": "Building something new",
            "current": "DeskSync is ready for you",
            "next": "Music, time and system light",
            "index": 1,
            "line_count": 4,
        },
    }


def demo_notification() -> dict[str, Any]:
    return {
        "id": "demo-notification",
        "title": "DeskSync Demo",
        "message": "The notification screen is working.",
        "source": "Demo Mode",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "read": False,
        "index": 0,
        "count": 1,
    }


def demo_device_state() -> dict[str, Any]:
    song = demo_song()
    system = demo_system()
    notification = demo_notification()

    return {
        "status": "online",
        "demo_mode": True,
        "timestamp": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "spotify": {
            "status": "online",
            "playing": song["playing"],
            "title": song["title"],
            "artist": song["artist"],
            "album": song["album"],
            "progress_ms": song["progress"],
            "duration_ms": song["duration"],
            "volume": song["volume"],
            "device": song["device"],
        },
        "system": {
            "status": "online",
            "cpu_percent": system["cpu"]["percent"],
            "memory_percent": system["memory"]["percent"],
            "disk_percent": system["disk"]["percent"],
            "uptime": system["uptime"]["readable"],
            "network_received_mb": (
                system["network"]["received_mb"]
            ),
            "network_sent_mb": (
                system["network"]["sent_mb"]
            ),
            "battery": system["battery"],
        },
        "notifications": {
            "status": "online",
            "unread_count": 1,
            "latest": notification,
        },
    }