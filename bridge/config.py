import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# Load credentials from bridge/.env
load_dotenv(BASE_DIR / ".env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8888/callback"
)

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise RuntimeError(
        "Spotify credentials are missing. "
        "Create bridge/.env and add SPOTIFY_CLIENT_ID and "
        "SPOTIFY_CLIENT_SECRET."
    )