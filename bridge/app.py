from flask import Flask, jsonify
from spotify import sp

app = Flask(__name__)

@app.route("/")
def home():
    return "Spotify Bridge Running!"

@app.route("/song")
def song():
    playback = sp.current_playback()

    if playback is None or playback["item"] is None:
        return jsonify({
            "status": "offline"
        })

    item = playback["item"]

    return jsonify({
        "status": "online",
        "playing": playback["is_playing"],
        "title": item["name"],
        "artist": item["artists"][0]["name"],
        "album": item["album"]["name"],
        "progress": playback["progress_ms"],
        "duration": item["duration_ms"],
        "volume": playback["device"]["volume_percent"]
    })


@app.route("/next")
def next_song():
    sp.next_track()
    return jsonify({"message": "Next Track"})


@app.route("/previous")
def previous_song():
    sp.previous_track()
    return jsonify({"message": "Previous Track"})


@app.route("/toggle")
def toggle():
    playback = sp.current_playback()

    if playback is None:
        return jsonify({"error": "No active device"}), 400

    if playback["is_playing"]:
        sp.pause_playback()
        return jsonify({"message": "Paused"})
    else:
        sp.start_playback()
        return jsonify({"message": "Playing"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)