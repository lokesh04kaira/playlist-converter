import tkinter as tk
from tkinter import messagebox
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from requests.exceptions import ReadTimeout, RequestException
import re

# Function to validate YouTube playlist URL
def validate_youtube_playlist_url(url):
    """Validate if the URL is a valid YouTube playlist URL."""
    if not url or not isinstance(url, str):
        return False, "Please enter a valid URL."
    
    # Check if it's a YouTube URL
    if "youtube.com" not in url and "youtu.be" not in url:
        return False, "Please enter a valid YouTube URL."
    
    # Check if it contains playlist ID
    if "list=" not in url:
        return False, "Please enter a valid YouTube playlist URL (must contain playlist ID)."
    
    return True, ""

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
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown API error")
            if "quota" in error_msg.lower():
                raise Exception("YouTube API quota exceeded. Please try again later.")
            elif "not found" in error_msg.lower():
                raise Exception("Playlist not found or is private.")
            else:
                raise Exception(f"YouTube API error: {error_msg}")
        
        return data
    except requests.exceptions.Timeout:
        messagebox.showerror("Error", "Request timed out. Please check your internet connection and try again.")
        return None
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Network error: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch YouTube playlist: {e}")
        return None

# Function to extract video titles
def extract_video_titles(youtube_data):
    if not youtube_data or "items" not in youtube_data:
        return []
    
    titles = []
    for item in youtube_data["items"]:
        if "snippet" in item and "title" in item["snippet"]:
            title = item["snippet"]["title"]
            # Clean up the title (remove common YouTube suffixes)
            title = re.sub(r'\s*\(Official Music Video\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Official Video\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Lyrics\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Audio\)', '', title, flags=re.IGNORECASE)
            titles.append(title.strip())
    
    return titles

# Function to authenticate with Spotify
def authenticate_spotify():
    try:
        sp_oauth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri="http://localhost:8888/callback",
            scope="playlist-modify-public playlist-modify-private",
            requests_timeout=30
        )
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        return sp
    except Exception as e:
        raise Exception(f"Spotify authentication failed: {e}")

# Function to search for Spotify tracks with retry logic
def search_spotify_tracks(sp, track_names, retries=3):
    track_uris = []
    found_tracks = 0
    total_tracks = len(track_names)
    
    for i, track_name in enumerate(track_names, 1):
        attempt = 0
        while attempt < retries:
            try:
                result = sp.search(q=track_name, type="track", limit=1)
                if result["tracks"]["items"]:
                    track_uris.append(result["tracks"]["items"][0]["uri"])
                    found_tracks += 1
                    print(f"Found track {i}/{total_tracks}: {track_name}")
                else:
                    print(f"No Spotify track found for: {track_name}")
                break
            except ReadTimeout:
                attempt += 1
                print(f"Timeout occurred while searching for: {track_name}. Retrying {attempt}/{retries}...")
                if attempt == retries:
                    print(f"Failed to find track after {retries} retries: {track_name}")
            except Exception as e:
                print(f"Error searching for {track_name}: {e}")
                break
    
    print(f"Successfully found {found_tracks}/{total_tracks} tracks on Spotify")
    return track_uris

# Function to create Spotify playlist
def create_spotify_playlist(sp, user_id, playlist_name="Converted YouTube Playlist"):
    try:
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description="Playlist converted from YouTube"
        )
        return playlist["id"]
    except Exception as e:
        raise Exception(f"Failed to create Spotify playlist: {e}")

# Function to add tracks to Spotify playlist
def add_tracks_to_spotify_playlist(sp, playlist_id, track_uris):
    try:
        if track_uris:
            sp.playlist_add_items(playlist_id, track_uris)
            return len(track_uris)
        return 0
    except Exception as e:
        raise Exception(f"Failed to add tracks to playlist: {e}")

# Main conversion logic
def convert_playlist():
    # Get the YouTube playlist link from the entry
    youtube_url = youtube_url_entry.get().strip()
    
    # Validate URL
    is_valid, error_msg = validate_youtube_playlist_url(youtube_url)
    if not is_valid:
        messagebox.showerror("Error", error_msg)
        return

    # Show progress message
    progress_label.config(text="Fetching YouTube playlist...")
    root.update()

    # Fetch YouTube playlist data
    youtube_data = fetch_youtube_playlist_data(youtube_url)
    if not youtube_data:
        progress_label.config(text="")
        return

    # Extract video titles
    video_titles = extract_video_titles(youtube_data)
    if not video_titles:
        messagebox.showerror("Error", "No videos found in the YouTube playlist.")
        progress_label.config(text="")
        return

    progress_label.config(text=f"Found {len(video_titles)} videos. Authenticating with Spotify...")
    root.update()

    # Authenticate with Spotify
    try:
        sp = authenticate_spotify()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        progress_label.config(text="")
        return

    progress_label.config(text="Searching for tracks on Spotify...")
    root.update()

    # Search for tracks on Spotify
    spotify_track_uris = search_spotify_tracks(sp, video_titles)
    if not spotify_track_uris:
        messagebox.showerror("Error", "No matching Spotify tracks found.")
        progress_label.config(text="")
        return

    progress_label.config(text="Creating Spotify playlist...")
    root.update()

    # Create Spotify playlist
    try:
        user_id = sp.me()["id"]
        playlist_id = create_spotify_playlist(sp, user_id)
        added_tracks = add_tracks_to_spotify_playlist(sp, playlist_id, spotify_track_uris)
        
        success_msg = f"Playlist converted successfully!\n\nAdded {added_tracks} tracks to Spotify playlist."
        messagebox.showinfo("Success", success_msg)
    except Exception as e:
        messagebox.showerror("Error", str(e))
    
    progress_label.config(text="")

# GUI setup
root = tk.Tk()
root.title("YouTube to Spotify Playlist Converter")
root.geometry("500x300")

# Window layout
tk.Label(root, text="Enter YouTube Playlist URL:", font=("Arial", 12)).pack(pady=10)
youtube_url_entry = tk.Entry(root, width=50, font=("Arial", 10))
youtube_url_entry.pack(pady=5)

convert_button = tk.Button(root, text="Convert to Spotify Playlist", command=convert_playlist, 
                          font=("Arial", 11), bg="#1DB954", fg="white", relief="flat", padx=20, pady=5)
convert_button.pack(pady=20)

progress_label = tk.Label(root, text="", font=("Arial", 10), fg="blue")
progress_label.pack(pady=10)

# Add some styling
root.configure(bg="#f0f0f0")
convert_button.configure(activebackground="#1ed760", activeforeground="white")

# Start the GUI loop
root.mainloop()
