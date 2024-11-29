import tkinter as tk
from tkinter import messagebox
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from requests.exceptions import ReadTimeout

# Function to fetch playlist data from YouTube
def fetch_youtube_playlist_data(playlist_url):
    try:
        # Extract playlist ID from the URL
        if "list=" in playlist_url:
            playlist_id = playlist_url.split("list=")[1].split("&")[0]
        else:
            raise ValueError("Invalid YouTube playlist URL.")
        
        # Call YouTube API
        url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&key={YOUTUBE_API_KEY}&maxResults=50"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch YouTube playlist: {e}")
        return None

# Function to extract video titles
def extract_video_titles(youtube_data):
    if not youtube_data or "items" not in youtube_data:
        return []
    return [item["snippet"]["title"] for item in youtube_data["items"]]

# Function to authenticate with Spotify
def authenticate_spotify():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri="http://localhost:8888/callback",
        scope="playlist-modify-public playlist-modify-private",
        requests_timeout=10  # Set a higher timeout for Spotify requests
    )
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    return sp

# Function to search for Spotify tracks with retry logic
def search_spotify_tracks(sp, track_names, retries=3):
    track_uris = []
    for track_name in track_names:
        attempt = 0
        while attempt < retries:
            try:
                result = sp.search(q=track_name, type="track", limit=1)
                if result["tracks"]["items"]:
                    track_uris.append(result["tracks"]["items"][0]["uri"])
                else:
                    print(f"No Spotify track found for: {track_name}")
                break
            except ReadTimeout:
                attempt += 1
                print(f"Timeout occurred while searching for: {track_name}. Retrying {attempt}/{retries}...")
        if attempt == retries:
            print(f"Failed to find track after {retries} retries: {track_name}")
    return track_uris

# Function to create Spotify playlist
def create_spotify_playlist(sp, user_id, playlist_name="Converted YouTube Playlist"):
    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=False,
        description="Playlist converted from YouTube"
    )
    return playlist["id"]

# Function to add tracks to Spotify playlist
def add_tracks_to_spotify_playlist(sp, playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)

# Main conversion logic
def convert_playlist():
    # Get the YouTube playlist link from the entry
    youtube_url = youtube_url_entry.get()
    if not youtube_url:
        messagebox.showerror("Error", "Please enter a YouTube playlist URL.")
        return

    # Fetch YouTube playlist data
    youtube_data = fetch_youtube_playlist_data(youtube_url)
    if not youtube_data:
        return

    # Extract video titles
    video_titles = extract_video_titles(youtube_data)
    if not video_titles:
        messagebox.showerror("Error", "No videos found in the YouTube playlist.")
        return

    # Authenticate with Spotify
    try:
        sp = authenticate_spotify()
    except Exception as e:
        messagebox.showerror("Error", f"Spotify authentication failed: {e}")
        return

    # Search for tracks on Spotify
    spotify_track_uris = search_spotify_tracks(sp, video_titles)
    if not spotify_track_uris:
        messagebox.showerror("Error", "No matching Spotify tracks found.")
        return

    # Create Spotify playlist
    try:
        user_id = sp.me()["id"]
        playlist_id = create_spotify_playlist(sp, user_id)
        add_tracks_to_spotify_playlist(sp, playlist_id, spotify_track_uris)
        messagebox.showinfo("Success", "Playlist converted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create Spotify playlist: {e}")

# GUI setup
root = tk.Tk()
root.title("YouTube to Spotify Playlist Converter")

# Window layout
tk.Label(root, text="Enter YouTube Playlist URL:").pack(pady=10)
youtube_url_entry = tk.Entry(root, width=50)
youtube_url_entry.pack(pady=5)

convert_button = tk.Button(root, text="Convert to Spotify Playlist", command=convert_playlist)
convert_button.pack(pady=20)

# Start the GUI loop
root.mainloop()
