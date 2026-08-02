from datetime import datetime

from flask import Flask, jsonify, request, render_template

from lyrics_service import (
    fetch_lyrics,
    get_plain_window,
    get_synced_window,
)
from spotify import sp
from system_monitor import get_system_stats
from notification_store import (
    add_notification,
    clear_notifications,
    database_connection,
    get_notification,
    mark_notification_read,
    unread_count,
)

app = Flask(__name__)


@app.route("/")
def home():
    return "DeskSync Bridge Running!"

@app.route("/health")
def health():
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

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")


@app.route("/song")
def song():
    playback = sp.current_playback()

    if playback is None or playback.get("item") is None:
        return jsonify({
            "status": "offline",
            "playing": False,
        })

    item = playback["item"]
    device = playback.get("device") or {}

    artists = item.get("artists") or []

    artist_name = ", ".join(
        artist.get("name", "")
        for artist in artists
        if artist.get("name")
    )

    album = item.get("album") or {}

    return jsonify({
        "status": "online",
        "playing": bool(
            playback.get("is_playing")
        ),
        "title": item.get("name", ""),
        "artist": artist_name,
        "album": album.get("name", ""),
        "progress": (
            playback.get("progress_ms") or 0
        ),
        "duration": (
            item.get("duration_ms") or 0
        ),
        "volume": device.get(
            "volume_percent"
        ),
        "device": device.get("name"),
    })


@app.route("/next")
def next_song():
    playback = sp.current_playback()

    if playback is None:
        return jsonify({
            "status": "error",
            "message": "No active Spotify device",
        }), 409

    sp.next_track()

    return jsonify({
        "status": "success",
        "message": "Next track",
    })


@app.route("/previous")
def previous_song():
    playback = sp.current_playback()

    if playback is None:
        return jsonify({
            "status": "error",
            "message": "No active Spotify device",
        }), 409

    sp.previous_track()

    return jsonify({
        "status": "success",
        "message": "Previous track",
    })


@app.route("/toggle")
def toggle():
    playback = sp.current_playback()

    if playback is None:
        return jsonify({
            "status": "error",
            "message": "No active Spotify device",
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


@app.route("/system")
def system_status():
    return jsonify({
        "status": "online",
        "pc": get_system_stats(),
    })


@app.route("/lyrics")
def current_lyrics():
    playback = sp.current_playback()

    if playback is None or playback.get("item") is None:
        return jsonify({
            "status": "offline",
            "message": "No active Spotify track",
        }), 404

    item = playback["item"]

    if item.get("type") != "track":
        return jsonify({
            "status": "unsupported",
            "message": (
                "Lyrics are supported only for songs."
            ),
        }), 400

    title = item.get("name", "")

    artists = item.get("artists") or []

    artist_name = ", ".join(
        artist.get("name", "")
        for artist in artists
        if artist.get("name")
    )

    album_data = item.get("album") or {}
    album_name = album_data.get("name", "")

    duration_ms = item.get("duration_ms") or 0
    progress_ms = (
        playback.get("progress_ms") or 0
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
            "message": lyrics_result["error"],
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
            lines=lyrics_result["plain_lines"],
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

@app.route("/notifications", methods=["GET"])
def notification_details():
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


@app.route("/notifications", methods=["POST"])
def create_notification():
    payload = request.get_json(
        silent=True
    ) or {}

    title = str(
        payload.get("title", "")
    ).strip()

    message = str(
        payload.get("message", "")
    ).strip()

    source = str(
        payload.get("source", "DeskSync")
    ).strip() or "DeskSync"

    if not title:
        return jsonify({
            "status": "error",
            "message": "Notification title is required.",
        }), 400

    if not message:
        return jsonify({
            "status": "error",
            "message": "Notification message is required.",
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


@app.route("/notifications/read", methods=["POST"])
def read_notification():
    payload = request.get_json(
        silent=True
    ) or {}

    notification_id = str(
        payload.get("id", "")
    ).strip()

    if not notification_id:
        return jsonify({
            "status": "error",
            "message": "Notification ID is required.",
        }), 400

    notification = mark_notification_read(
        notification_id
    )

    if notification is None:
        return jsonify({
            "status": "not_found",
            "message": "Notification was not found.",
        }), 404

    return jsonify({
        "status": "success",
        "notification": notification,
        "unread_count": unread_count(),
    })


@app.route("/notifications", methods=["DELETE"])
def delete_all_notifications():
    deleted_count = clear_notifications()

    return jsonify({
        "status": "success",
        "deleted_count": deleted_count,
        "unread_count": 0,
    })
if __name__ == "__main__":
        app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
)