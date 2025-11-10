# main.py (improved)
import tkinter as tk
from tkinter import messagebox
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from requests.exceptions import ReadTimeout, RequestException
import re
import webbrowser
import time
from datetime import datetime

# ---------- Config / constants ----------
REDIRECT_URI = "http://localhost:8888/callback"  # must match Spotify App redirect URI
SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private"
SPOTIFY_CACHE_PATH = ".spotify_token_cache"

# ---------- Utility functions ----------
def validate_youtube_playlist_url(url):
    if not url or not isinstance(url, str):
        return False, "Please enter a valid URL."
    if "youtube.com" not in url and "youtu.be" not in url:
        return False, "Please enter a valid YouTube URL."
    if "list=" not in url:
        return False, "Please enter a valid YouTube playlist URL (must contain playlist ID)."
    return True, ""

def fetch_youtube_playlist_data(playlist_url):
    """
    Fetch all playlist items using pagination (maxResults=50 per page).
    Returns dict with key "items" or None on error (shows messagebox).
    """
    try:
        if "list=" in playlist_url:
            playlist_id = playlist_url.split("list=")[1].split("&")[0]
        else:
            raise ValueError("Invalid YouTube playlist URL.")
        
        base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "key": YOUTUBE_API_KEY,
            "maxResults": 50
        }
        all_items = []
        while True:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                if "quota" in error_msg.lower():
                    raise Exception("YouTube API quota exceeded. Please try again later.")
                elif "not found" in error_msg.lower():
                    raise Exception("Playlist not found or is private.")
                else:
                    raise Exception(f"YouTube API error: {error_msg}")
            items = data.get("items", [])
            all_items.extend(items)
            next_tok = data.get("nextPageToken")
            if not next_tok:
                break
            params["pageToken"] = next_tok
        return {"items": all_items}
    except ReadTimeout:
        messagebox.showerror("Error", "Request timed out. Please check your internet connection and try again.")
        return None
    except RequestException as e:
        messagebox.showerror("Error", f"Network error: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch YouTube playlist: {e}")
        return None

def extract_video_titles(youtube_data):
    if not youtube_data or "items" not in youtube_data:
        return []
    titles = []
    for item in youtube_data["items"]:
        snippet = item.get("snippet", {})
        title = snippet.get("title")
        if title:
            title = re.sub(r'\s*\(Official Music Video\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Official Video\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Lyrics\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Audio\)', '', title, flags=re.IGNORECASE)
            titles.append(title.strip())
    return titles

# ---------- Spotify auth & helper ----------
def make_sp_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SPOTIFY_SCOPE,
        cache_path=SPOTIFY_CACHE_PATH,
        show_dialog=False
    )

def authenticate_spotify_via_browser(parent_window, timeout=120):
    """
    If cached token exists, returns spotipy.Spotify object.
    Otherwise opens browser for user to authorize and waits (poll) for cached token.
    """
    sp_oauth = make_sp_oauth()
    token_info = sp_oauth.get_cached_token()

    if token_info and token_info.get("access_token"):
        return spotipy.Spotify(auth=token_info["access_token"])

    # No cached token -> open browser to authorize
    auth_url = sp_oauth.get_authorize_url()
    try:
        webbrowser.open(auth_url, new=1)
    except Exception:
        # fallback: show URL to user
        messagebox.showinfo("Authenticate Spotify", f"Please open this URL in your browser to authorize:\n\n{auth_url}")

    # Ask user to complete auth in browser
    msg = ("A browser window should have opened for Spotify authentication.\n\n"
           "Please log in and allow the app. After that, return here and click OK.\n\n"
           "If the browser didn't open, paste the URL into your browser manually.")
    if not messagebox.askokcancel("Spotify Authentication", msg):
        raise Exception("Spotify authentication cancelled by user.")

    # Poll for cached token for up to `timeout` seconds
    waited = 0
    poll_interval = 1
    while waited < timeout:
        token_info = sp_oauth.get_cached_token()
        if token_info and token_info.get("access_token"):
            return spotipy.Spotify(auth=token_info["access_token"])
        time.sleep(poll_interval)
        waited += poll_interval

    raise Exception("Timed out waiting for Spotify authentication. Please try again.")

# ---------- Spotify search/create/add ----------
def search_spotify_tracks(sp, track_names, retries=3):
    track_uris = []
    found_tracks = 0
    total_tracks = len(track_names)

    for i, track_name in enumerate(track_names, 1):
        attempt = 0
        while attempt < retries:
            try:
                result = sp.search(q=track_name, type="track", limit=1)
                items = result.get("tracks", {}).get("items", [])
                if items:
                    track_uris.append(items[0]["uri"])
                    found_tracks += 1
                    print(f"Found track {i}/{total_tracks}: {track_name}")
                else:
                    print(f"No Spotify track found for: {track_name}")
                break
            except ReadTimeout:
                attempt += 1
                print(f"Timeout for '{track_name}', retry {attempt}/{retries}...")
                if attempt == retries:
                    print(f"Giving up on: {track_name}")
            except Exception as e:
                print(f"Error searching for {track_name}: {e}")
                break

    print(f"Found {found_tracks}/{total_tracks} tracks on Spotify.")
    return track_uris

def create_spotify_playlist(sp, user_id, playlist_name="Converted YouTube Playlist"):
    try:
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description=f"Converted from YouTube on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return playlist["id"]
    except Exception as e:
        raise Exception(f"Failed to create Spotify playlist: {e}")

def add_tracks_to_spotify_playlist(sp, playlist_id, track_uris):
    """
    Add tracks in batches of 100 (Spotify limit).
    Returns number of successfully added tracks (attempted).
    """
    try:
        if not track_uris:
            return 0
        batch_size = 100
        added = 0
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i+batch_size]
            sp.playlist_add_items(playlist_id, batch)
            added += len(batch)
        return added
    except Exception as e:
        raise Exception(f"Failed to add tracks to playlist: {e}")

# ---------- GUI conversion flow ----------
def convert_playlist():
    youtube_url = youtube_url_entry.get().strip()
    is_valid, error_msg = validate_youtube_playlist_url(youtube_url)
    if not is_valid:
        messagebox.showerror("Error", error_msg)
        return

    progress_label.config(text="Fetching YouTube playlist...")
    root.update()

    youtube_data = fetch_youtube_playlist_data(youtube_url)
    if not youtube_data:
        progress_label.config(text="")
        return

    video_titles = extract_video_titles(youtube_data)
    if not video_titles:
        messagebox.showerror("Error", "No videos found in the YouTube playlist.")
        progress_label.config(text="")
        return

    progress_label.config(text=f"Found {len(video_titles)} videos. Authenticating with Spotify...")
    root.update()

    try:
        sp = authenticate_spotify_via_browser(root)
    except Exception as e:
        messagebox.showerror("Error", f"Spotify auth failed: {e}")
        progress_label.config(text="")
        return

    progress_label.config(text="Searching for tracks on Spotify...")
    root.update()

    spotify_track_uris = search_spotify_tracks(sp, video_titles)
    if not spotify_track_uris:
        messagebox.showerror("Error", "No matching Spotify tracks found.")
        progress_label.config(text="")
        return

    progress_label.config(text="Creating Spotify playlist...")
    root.update()

    try:
        user_id = sp.me().get("id")
        playlist_id = create_spotify_playlist(sp, user_id)
        added_tracks = add_tracks_to_spotify_playlist(sp, playlist_id, spotify_track_uris)

        messagebox.showinfo("Success", f"Playlist converted successfully!\n\nAdded {added_tracks} tracks.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    progress_label.config(text="")

# ---------- GUI ----------
root = tk.Tk()
root.title("YouTube to Spotify Playlist Converter")
root.geometry("560x320")

tk.Label(root, text="Enter YouTube Playlist URL:", font=("Arial", 12)).pack(pady=10)
youtube_url_entry = tk.Entry(root, width=70, font=("Arial", 10))
youtube_url_entry.pack(pady=5)

convert_button = tk.Button(root, text="Convert to Spotify Playlist", command=convert_playlist,
                          font=("Arial", 11), bg="#1DB954", fg="white", relief="flat", padx=20, pady=5)
convert_button.pack(pady=20)

progress_label = tk.Label(root, text="", font=("Arial", 10), fg="blue")
progress_label.pack(pady=10)

root.configure(bg="#f0f0f0")
convert_button.configure(activebackground="#1ed760", activeforeground="white")

root.mainloop()
