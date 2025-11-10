# auth_server.py
from flask import Flask, request
from spotipy.oauth2 import SpotifyOAuth
import time
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

REDIRECT_URI = "http://localhost:8888/callback"
CACHE_PATH = ".spotify_token_cache"

app = Flask(__name__)

def make_sp_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="playlist-modify-public playlist-modify-private",
        cache_path=CACHE_PATH,
        show_dialog=False
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error:
        return f"Auth error: {error}", 400
    if not code:
        return "No code received", 400
    sp_oauth = make_sp_oauth()
    # exchange code for token; different spotipy versions have slightly different signatures
    try:
        try:
            sp_oauth.get_access_token(code)
        except TypeError:
            sp_oauth.get_access_token(code, as_dict=True)
        return "Authorization complete. You can close this page and return to the app.", 200
    except Exception as e:
        return f"Token exchange failed: {e}", 500

if __name__ == "__main__":
    print("Starting local auth server on http://localhost:8888 ...")
    app.run(host="0.0.0.0", port=8888, debug=False)
