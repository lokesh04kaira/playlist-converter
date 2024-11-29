# Playlist Converter

## Description 📄
The Playlist Converter is a tool that allows users to convert a YouTube playlist into a Spotify playlist. This tool extracts the titles from the YouTube playlist, searches for the corresponding tracks on Spotify, and creates a new playlist on Spotify with those tracks.

## Features ✨
- Convert a YouTube playlist to a Spotify playlist.
- Seamless integration with YouTube and Spotify APIs.
- Easy-to-use interface using Tkinter for user input.
- Simple and efficient handling of YouTube and Spotify data.

## Requirements 📋
Before running this tool, ensure that you have the following installed on your local machine:
- Python 3.x
- pip (Python's package installer)

### Install Required Libraries:
`pip install -r requirements.txt`

## How to Use 🛠️

### 1. Clone the repository:
`git clone https://github.com/mriganshu16/playlist-converter.git`

### 2. Install the necessary dependencies:
`cd playlist-converter`
`pip install -r requirements.txt`

### 3. Set up your API keys:
You will need a YouTube API key and Spotify API credentials (Client ID and Client Secret).
- Add your API keys in the `config.py` file or set them as environment variables.

### 4. Run the application:
`python main.py`

A window will pop up asking for the YouTube playlist link. Enter the link, and the tool will fetch the playlist and create a new playlist on your Spotify account.

## Troubleshooting 🛠️
If you encounter any issues while running the tool, consider the following steps:

### 1. API Keys
Ensure that your YouTube API key and Spotify API credentials are correctly added in the `config.py` file or set as environment variables.

### 2. Internet Connection
A stable internet connection is required to connect to both the YouTube and Spotify APIs. Make sure you're connected to the internet.

### 3. Timeout Issues
If you encounter timeout errors, you can try increasing the timeout period in the code or checking the network.
ability.

4. Playlist Not Found
If the tool is unable to find tracks in the Spotify search, ensure that the titles in the YouTube playlist match the actual track names as closely as possible. You can also manually edit the playlist titles for better accuracy.
