import os

from datetime import datetime
from functools import wraps
from hmac import compare_digest
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from demo_data import (
    demo_device_state,
    demo_lyrics,
    demo_notification,
    demo_song,
    demo_system,
)
from lyrics_service import (
    fetch_lyrics,
    get_plain_window,
    get_synced_window,
)
from notification_store import (
    add_notification,
    clear_notifications,
    database_connection,
    get_notification,
    mark_notification_read,
    unread_count,
)
from spotify import sp
from system_monitor import get_system_stats


# ---------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------

ENV_PATH = (
    Path(__file__).resolve().parent
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True,
)


DEMO_MODE = (
    os.getenv(
        "DESKSYNC_DEMO_MODE",
        "false",
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)


DESKSYNC_API_KEY = os.getenv(
    "DESKSYNC_API_KEY",
    "",
).strip()


LOCAL_ADDRESSES = {
    "127.0.0.1",
    "::1",
}


demo_notification_is_read = False


app = Flask(__name__)


# ---------------------------------------------------------
# API security
# ---------------------------------------------------------

def require_api_key(view_function):
    """Require a valid DeskSync API key."""

    @wraps(view_function)
    def protected_view(*args, **kwargs):
        if not DESKSYNC_API_KEY:
            return jsonify({
                "status": "error",
                "message": (
                    "DeskSync API key is not configured."
                ),
            }), 503

        supplied_key = request.headers.get(
            "X-DeskSync-Key",
            "",
        ).strip()

        if (
            not supplied_key
            or not compare_digest(
                supplied_key,
                DESKSYNC_API_KEY,
            )
        ):
            return jsonify({
                "status": "unauthorized",
                "message": (
                    "A valid X-DeskSync-Key "
                    "header is required."
                ),
            }), 401

        return view_function(
            *args,
            **kwargs,
        )

    return protected_view


# ---------------------------------------------------------
# Basic routes
# ---------------------------------------------------------

@app.route("/")
def home():
    return "DeskSync Bridge Running!"


@app.route("/health")
def health():
    if DEMO_MODE:
        return jsonify({
            "status": "online",
            "demo_mode": True,
            "timestamp": (
                datetime.now()
                .astimezone()
                .isoformat(timespec="seconds")
            ),
            "components": {
                "bridge": True,
                "spotify": True,
                "database": True,
                "system_monitor": True,
            },
        })

    components = {
        "bridge": True,
        "spotify": False,
        "database": False,
        "system_monitor": False,
    }

    errors = {}

    try:
        sp.current_playback()
        components["spotify"] = True

    except Exception as error:
        errors["spotify"] = str(error)

    try:
        with database_connection() as connection:
            connection.execute(
                "SELECT 1"
            ).fetchone()

        components["database"] = True

    except Exception as error:
        errors["database"] = str(error)

    try:
        system_stats = get_system_stats()

        components["system_monitor"] = bool(
            system_stats
        )

    except Exception as error:
        errors["system_monitor"] = str(error)

    overall_status = (
        "online"
        if all(components.values())
        else "degraded"
    )

    response = {
        "status": overall_status,
        "timestamp": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "components": components,
    }

    if errors:
        response["errors"] = errors

    return jsonify(response)


# ---------------------------------------------------------
# Combined ESP32 device state
# ---------------------------------------------------------

@app.route("/device-state")
@require_api_key
def device_state():
    if DEMO_MODE:
        return jsonify(
            demo_device_state()
        )

    response = {
        "status": "online",
        "timestamp": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "spotify": {
            "status": "offline",
            "playing": False,
        },
        "system": None,
        "notifications": {
            "status": "online",
            "unread_count": 0,
            "latest": None,
        },
    }

    component_errors = {}

    # Spotify information
    try:
        playback = sp.current_playback()

        if (
            playback is not None
            and playback.get("item") is not None
        ):
            item = playback["item"]

            artists = (
                item.get("artists")
                or []
            )

            album = (
                item.get("album")
                or {}
            )

            device = (
                playback.get("device")
                or {}
            )

            artist_name = ", ".join(
                artist.get("name", "")
                for artist in artists
                if artist.get("name")
            )

            response["spotify"] = {
                "status": "online",
                "playing": bool(
                    playback.get("is_playing")
                ),
                "title": item.get(
                    "name",
                    "",
                ),
                "artist": artist_name,
                "album": album.get(
                    "name",
                    "",
                ),
                "progress_ms": (
                    playback.get("progress_ms")
                    or 0
                ),
                "duration_ms": (
                    item.get("duration_ms")
                    or 0
                ),
                "volume": device.get(
                    "volume_percent"
                ),
                "device": device.get(
                    "name"
                ),
            }

    except Exception as error:
        response["spotify"] = {
            "status": "error",
            "playing": False,
        }

        component_errors["spotify"] = str(
            error
        )

    # PC system information
    try:
        system_stats = get_system_stats()

        cpu = (
            system_stats.get("cpu")
            or {}
        )

        memory = (
            system_stats.get("memory")
            or {}
        )

        disk = (
            system_stats.get("disk")
            or {}
        )

        network = (
            system_stats.get("network")
            or {}
        )

        uptime = (
            system_stats.get("uptime")
            or {}
        )

        battery = system_stats.get(
            "battery"
        )

        response["system"] = {
            "status": "online",
            "cpu_percent": cpu.get(
                "percent"
            ),
            "memory_percent": memory.get(
                "percent"
            ),
            "disk_percent": disk.get(
                "percent"
            ),
            "uptime": uptime.get(
                "readable"
            ),
            "network_received_mb": (
                network.get("received_mb")
            ),
            "network_sent_mb": (
                network.get("sent_mb")
            ),
            "battery": battery,
        }

    except Exception as error:
        response["system"] = {
            "status": "error",
        }

        component_errors["system"] = str(
            error
        )

    # Notification information
    try:
        latest_notification = (
            get_notification(0)
        )

        latest_data = None

        if latest_notification is not None:
            latest_data = {
                "id": latest_notification.get(
                    "id"
                ),
                "title": latest_notification.get(
                    "title"
                ),
                "message": latest_notification.get(
                    "message"
                ),
                "source": latest_notification.get(
                    "source"
                ),
                "created_at": (
                    latest_notification.get(
                        "created_at"
                    )
                ),
                "read": latest_notification.get(
                    "read"
                ),
            }

        response["notifications"] = {
            "status": "online",
            "unread_count": unread_count(),
            "latest": latest_data,
        }

    except Exception as error:
        response["notifications"] = {
            "status": "error",
            "unread_count": 0,
            "latest": None,
        }

        component_errors[
            "notifications"
        ] = str(error)

    if component_errors:
        response["status"] = "degraded"
        response["errors"] = (
            component_errors
        )

    return jsonify(response)


# ---------------------------------------------------------
# Browser simulator
# ---------------------------------------------------------

@app.route("/simulator")
def simulator():
    if request.remote_addr not in LOCAL_ADDRESSES:
        return jsonify({
            "status": "forbidden",
            "message": (
                "The DeskSync simulator is "
                "available only on the local "
                "computer."
            ),
        }), 403

    return render_template(
        "simulator.html",
        api_key=DESKSYNC_API_KEY,
    )


# ---------------------------------------------------------
# Spotify information and controls
# ---------------------------------------------------------

@app.route("/song")
@require_api_key
def song():
    if DEMO_MODE:
        return jsonify({
            **demo_song(),
            "demo_mode": True,
        })

    playback = sp.current_playback()

    if (
        playback is None
        or playback.get("item") is None
    ):
        return jsonify({
            "status": "offline",
            "playing": False,
        })

    item = playback["item"]

    device = (
        playback.get("device")
        or {}
    )

    artists = (
        item.get("artists")
        or []
    )

    artist_name = ", ".join(
        artist.get("name", "")
        for artist in artists
        if artist.get("name")
    )

    album = (
        item.get("album")
        or {}
    )

    return jsonify({
        "status": "online",
        "playing": bool(
            playback.get("is_playing")
        ),
        "title": item.get(
            "name",
            "",
        ),
        "artist": artist_name,
        "album": album.get(
            "name",
            "",
        ),
        "progress": (
            playback.get("progress_ms")
            or 0
        ),
        "duration": (
            item.get("duration_ms")
            or 0
        ),
        "volume": device.get(
            "volume_percent"
        ),
        "device": device.get(
            "name"
        ),
    })


@app.route("/next")
@require_api_key
def next_song():
    if DEMO_MODE:
        return jsonify({
            "status": "success",
            "demo_mode": True,
            "message": "Demo next track",
        })

    playback = sp.current_playback()

    if playback is None:
        return jsonify({
            "status": "error",
            "message": (
                "No active Spotify device"
            ),
        }), 409

    sp.next_track()

    return jsonify({
        "status": "success",
        "message": "Next track",
    })


@app.route("/previous")
@require_api_key
def previous_song():
    if DEMO_MODE:
        return jsonify({
            "status": "success",
            "demo_mode": True,
            "message": "Demo previous track",
        })

    playback = sp.current_playback()

    if playback is None:
        return jsonify({
            "status": "error",
            "message": (
                "No active Spotify device"
            ),
        }), 409

    sp.previous_track()

    return jsonify({
        "status": "success",
        "message": "Previous track",
    })


@app.route("/toggle")
@require_api_key
def toggle():
    if DEMO_MODE:
        return jsonify({
            "status": "success",
            "demo_mode": True,
            "playing": True,
            "message": "Demo playback toggled",
        })

    playback = sp.current_playback()

    if playback is None:
        return jsonify({
            "status": "error",
            "message": (
                "No active Spotify device"
            ),
        }), 409

    if playback.get("is_playing"):
        sp.pause_playback()

        return jsonify({
            "status": "success",
            "playing": False,
            "message": "Paused",
        })

    sp.start_playback()

    return jsonify({
        "status": "success",
        "playing": True,
        "message": "Playing",
    })


# ---------------------------------------------------------
# PC system monitor
# ---------------------------------------------------------

@app.route("/system")
@require_api_key
def system_status():
    if DEMO_MODE:
        return jsonify({
            "status": "online",
            "demo_mode": True,
            "pc": demo_system(),
        })

    return jsonify({
        "status": "online",
        "pc": get_system_stats(),
    })


# ---------------------------------------------------------
# Lyrics
# ---------------------------------------------------------

@app.route("/lyrics")
@require_api_key
def current_lyrics():
    if DEMO_MODE:
        return jsonify({
            **demo_lyrics(),
            "demo_mode": True,
        })

    playback = sp.current_playback()

    if (
        playback is None
        or playback.get("item") is None
    ):
        return jsonify({
            "status": "offline",
            "message": (
                "No active Spotify track"
            ),
        }), 404

    item = playback["item"]

    if item.get("type") != "track":
        return jsonify({
            "status": "unsupported",
            "message": (
                "Lyrics are supported only "
                "for songs."
            ),
        }), 400

    title = item.get(
        "name",
        "",
    )

    artists = (
        item.get("artists")
        or []
    )

    artist_name = ", ".join(
        artist.get("name", "")
        for artist in artists
        if artist.get("name")
    )

    album_data = (
        item.get("album")
        or {}
    )

    album_name = album_data.get(
        "name",
        "",
    )

    duration_ms = (
        item.get("duration_ms")
        or 0
    )

    progress_ms = (
        playback.get("progress_ms")
        or 0
    )

    lyrics_result = fetch_lyrics(
        title=title,
        artist=artist_name,
        album=album_name,
        duration_ms=duration_ms,
    )

    if not lyrics_result["available"]:
        return jsonify({
            "status": "not_found",
            "title": title,
            "artist": artist_name,
            "message": lyrics_result[
                "error"
            ],
        }), 404

    requested_index = request.args.get(
        "index",
        default=None,
        type=int,
    )

    synced_lines = lyrics_result[
        "synced_lines"
    ]

    if synced_lines:
        lyric_window = get_synced_window(
            lines=synced_lines,
            progress_ms=progress_ms,
            requested_index=requested_index,
        )

        lyrics_type = "synced"

        mode = (
            "automatic"
            if requested_index is None
            else "manual"
        )

    else:
        lyric_window = get_plain_window(
            lines=lyrics_result[
                "plain_lines"
            ],
            requested_index=requested_index,
        )

        lyrics_type = "plain"
        mode = "manual"

    return jsonify({
        "status": "online",
        "title": title,
        "artist": artist_name,
        "album": album_name,
        "playing": bool(
            playback.get("is_playing")
        ),
        "progress_ms": progress_ms,
        "duration_ms": duration_ms,
        "instrumental": lyrics_result[
            "instrumental"
        ],
        "lyrics_type": lyrics_type,
        "mode": mode,
        "lyrics": lyric_window,
    })


# ---------------------------------------------------------
# Notifications
# ---------------------------------------------------------

@app.route(
    "/notifications",
    methods=["GET"],
)
@require_api_key
def notification_details():
    if DEMO_MODE:
        notification = (
            demo_notification()
        )

        notification["read"] = (
            demo_notification_is_read
        )

        return jsonify({
            "status": "online",
            "demo_mode": True,
            "notification": notification,
            "unread_count": (
                0
                if demo_notification_is_read
                else 1
            ),
        })

    notification_index = request.args.get(
        "index",
        default=0,
        type=int,
    )

    notification = get_notification(
        notification_index
    )

    if notification is None:
        return jsonify({
            "status": "empty",
            "notification": None,
            "unread_count": 0,
        })

    return jsonify({
        "status": "online",
        "notification": notification,
        "unread_count": unread_count(),
    })


@app.route(
    "/notifications",
    methods=["POST"],
)
@require_api_key
def create_notification():
    payload = request.get_json(
        silent=True
    ) or {}

    title = str(
        payload.get(
            "title",
            "",
        )
    ).strip()

    message = str(
        payload.get(
            "message",
            "",
        )
    ).strip()

    source = str(
        payload.get(
            "source",
            "DeskSync",
        )
    ).strip() or "DeskSync"

    if not title:
        return jsonify({
            "status": "error",
            "message": (
                "Notification title "
                "is required."
            ),
        }), 400

    if not message:
        return jsonify({
            "status": "error",
            "message": (
                "Notification message "
                "is required."
            ),
        }), 400

    notification = add_notification(
        title=title,
        message=message,
        source=source,
    )

    return jsonify({
        "status": "created",
        "notification": notification,
        "unread_count": unread_count(),
    }), 201


@app.route(
    "/notifications/read",
    methods=["POST"],
)
@require_api_key
def read_notification():
    global demo_notification_is_read

    payload = request.get_json(
        silent=True
    ) or {}

    notification_id = str(
        payload.get(
            "id",
            "",
        )
    ).strip()

    if (
        DEMO_MODE
        and notification_id
        == "demo-notification"
    ):
        demo_notification_is_read = True

        notification = (
            demo_notification()
        )

        notification["read"] = True

        return jsonify({
            "status": "success",
            "demo_mode": True,
            "notification": notification,
            "unread_count": 0,
        })

    if not notification_id:
        return jsonify({
            "status": "error",
            "message": (
                "Notification ID is required."
            ),
        }), 400

    notification = mark_notification_read(
        notification_id
    )

    if notification is None:
        return jsonify({
            "status": "not_found",
            "message": (
                "Notification was not found."
            ),
        }), 404

    return jsonify({
        "status": "success",
        "notification": notification,
        "unread_count": unread_count(),
    })


@app.route(
    "/notifications",
    methods=["DELETE"],
)
@require_api_key
def delete_all_notifications():
    deleted_count = clear_notifications()

    return jsonify({
        "status": "success",
        "deleted_count": deleted_count,
        "unread_count": 0,
    })


# ---------------------------------------------------------
# Start Flask
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )