from flask import Flask, render_template, request, jsonify, session
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from requests.exceptions import ReadTimeout, RequestException
import re
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
        raise Exception("Request timed out. Please check your internet connection and try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")
    except Exception as e:
        raise Exception(f"Failed to fetch YouTube playlist: {e}")

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

# Function to search for Spotify tracks
def search_spotify_tracks(sp, track_names):
    track_uris = []
    found_tracks = 0
    total_tracks = len(track_names)
    
    for i, track_name in enumerate(track_names, 1):
        try:
            result = sp.search(q=track_name, type="track", limit=1)
            if result["tracks"]["items"]:
                track_uris.append(result["tracks"]["items"][0]["uri"])
                found_tracks += 1
            else:
                print(f"No Spotify track found for: {track_name}")
        except Exception as e:
            print(f"Error searching for {track_name}: {e}")
    
    return track_uris, found_tracks, total_tracks

# Function to create Spotify playlist
def create_spotify_playlist(sp, user_id, playlist_name):
    try:
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description=f"Playlist converted from YouTube on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_playlist():
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url', '').strip()
        playlist_name = data.get('playlist_name', 'Converted YouTube Playlist').strip()
        
        if not playlist_name:
            playlist_name = 'Converted YouTube Playlist'
        
        # Validate URL
        is_valid, error_msg = validate_youtube_playlist_url(youtube_url)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg})
        
        # Fetch YouTube playlist data
        youtube_data = fetch_youtube_playlist_data(youtube_url)
        
        # Extract video titles
        video_titles = extract_video_titles(youtube_data)
        if not video_titles:
            return jsonify({'success': False, 'error': 'No videos found in the YouTube playlist.'})
        
        # Authenticate with Spotify
        try:
            sp_oauth = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri="http://localhost:5000/callback",
                scope="playlist-modify-public playlist-modify-private",
                requests_timeout=30
            )
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Spotify authentication failed: {e}'})
        
        # Search for tracks on Spotify
        spotify_track_uris, found_tracks, total_tracks = search_spotify_tracks(sp, video_titles)
        if not spotify_track_uris:
            return jsonify({'success': False, 'error': 'No matching Spotify tracks found.'})
        
        # Create Spotify playlist
        user_id = sp.me()["id"]
        playlist_id = create_spotify_playlist(sp, user_id, playlist_name)
        added_tracks = add_tracks_to_spotify_playlist(sp, playlist_id, spotify_track_uris)
        
        return jsonify({
            'success': True,
            'message': f'Playlist converted successfully! Added {added_tracks} tracks to Spotify playlist.',
            'stats': {
                'total_videos': total_tracks,
                'found_tracks': found_tracks,
                'added_tracks': added_tracks
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/callback')
def callback():
    return render_template('callback.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 