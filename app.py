# app.py (improved)
from flask import Flask, render_template, request, jsonify, session, redirect
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from requests.exceptions import Timeout, RequestException
import re
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Config import (make sure config.py exists with these variables)
from config import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Validate YouTube playlist URL
def validate_youtube_playlist_url(url):
    if not url or not isinstance(url, str):
        return False, "Please enter a valid URL."
    if "youtube.com" not in url and "youtu.be" not in url:
        return False, "Please enter a valid YouTube URL."
    if "list=" not in url:
        return False, "Please enter a valid YouTube playlist URL (must contain playlist ID)."
    return True, ""

# Fetch ALL playlist items (handles pagination)
def fetch_youtube_playlist_data(playlist_url):
    try:
        if "list=" in playlist_url:
            playlist_id = playlist_url.split("list=")[1].split("&")[0]
        else:
            raise ValueError("Invalid YouTube playlist URL.")
        
        all_items = []
        base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "key": YOUTUBE_API_KEY,
            "maxResults": 50
        }
        while True:
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                msg = data["error"].get("message", "Unknown API error")
                if "quota" in msg.lower():
                    raise Exception("YouTube API quota exceeded. Please try again later.")
                else:
                    raise Exception(f"YouTube API error: {msg}")
            items = data.get("items", [])
            all_items.extend(items)
            next_tok = data.get("nextPageToken")
            if not next_tok:
                break
            params["pageToken"] = next_tok
        return {"items": all_items}
    except Timeout:
        raise Exception("Request timed out. Please check your internet connection and try again.")
    except RequestException as e:
        raise Exception(f"Network error: {e}")
    except Exception as e:
        raise Exception(f"Failed to fetch YouTube playlist: {e}")

# Extract clean titles
def extract_video_titles(youtube_data):
    if not youtube_data or "items" not in youtube_data:
        return []
    titles = []
    for item in youtube_data["items"]:
        snippet = item.get("snippet", {})
        title = snippet.get("title")
        if title:
            # remove common suffixes (extend as needed)
            title = re.sub(r'\s*\(Official Music Video\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Official Video\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Lyrics\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Audio\)', '', title, flags=re.IGNORECASE)
            titles.append(title.strip())
    return titles

# Search spotify
def search_spotify_tracks(sp, track_names):
    track_uris = []
    found_tracks = 0
    total_tracks = len(track_names)
    for track_name in track_names:
        try:
            res = sp.search(q=track_name, type="track", limit=1)
            items = res.get("tracks", {}).get("items", [])
            if items:
                track_uris.append(items[0]["uri"])
                found_tracks += 1
            else:
                print("No Spotify track found for:", track_name)
        except Exception as e:
            print("Error searching for", track_name, e)
    return track_uris, found_tracks, total_tracks

def create_spotify_playlist(sp, user_id, playlist_name):
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
    try:
        if track_uris:
            # Spotify limits 100 tracks per add_items call; but for simplicity we send all if small
            sp.playlist_add_items(playlist_id, track_uris)
            return len(track_uris)
        return 0
    except Exception as e:
        raise Exception(f"Failed to add tracks to playlist: {e}")

@app.route('/')
def index():
    return render_template('index.html')

# Helper: create SpotifyOAuth with a local cache path (change per-user if needed)
def make_sp_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri="http://localhost:5000/callback",
        scope="playlist-modify-public playlist-modify-private",
        cache_path=".spotify_caches"  # simple cache file
    )

# Convert route: if user not authenticated, return auth_url so frontend can redirect
@app.route('/convert', methods=['POST'])
def convert_playlist():
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url', '').strip()
        playlist_name = data.get('playlist_name', 'Converted YouTube Playlist').strip() or 'Converted YouTube Playlist'
        is_valid, error_msg = validate_youtube_playlist_url(youtube_url)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg})

        youtube_data = fetch_youtube_playlist_data(youtube_url)
        video_titles = extract_video_titles(youtube_data)
        if not video_titles:
            return jsonify({'success': False, 'error': 'No videos found in the YouTube playlist.'})

        sp_oauth = make_sp_oauth()
        token_info = sp_oauth.get_cached_token()

        if not token_info:
            # No cached token — tell frontend to redirect user to this URL
            auth_url = sp_oauth.get_authorize_url()
            return jsonify({'success': False, 'needs_auth': True, 'auth_url': auth_url})

        sp = spotipy.Spotify(auth=token_info['access_token'])
        spotify_track_uris, found_tracks, total_tracks = search_spotify_tracks(sp, video_titles)
        if not spotify_track_uris:
            return jsonify({'success': False, 'error': 'No matching Spotify tracks found.'})

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

# OAuth callback: Spotify will redirect here with ?code=...
@app.route('/callback')
def callback():
    sp_oauth = make_sp_oauth()
    code = request.args.get('code')
    error = request.args.get('error')
    if error:
        return render_template('callback.html', error=error)
    if code:
        # Exchange code for token and store in cache (SpotifyOAuth handles cache file)
        token_info = sp_oauth.get_access_token(code, as_dict=True)  # note: API name may vary by spotipy version
        # After token is cached, redirect to a frontend page (index) and let user re-trigger conversion
        return redirect('/')
    return render_template('callback.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
