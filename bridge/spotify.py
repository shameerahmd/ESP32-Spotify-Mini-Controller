import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *

scope = "user-read-playback-state user-modify-playback-state"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
    )
)

def current_song():
    playback = sp.current_playback()

    if playback and playback["is_playing"]:
        song = playback["item"]["name"]
        artist = playback["item"]["artists"][0]["name"]
        print(f"Now Playing: {song} - {artist}")
    else:
        print("Nothing is currently playing.")