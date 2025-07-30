# Playlist Converter

## Description 📄

The Playlist Converter is a tool that allows users to convert a YouTube playlist into a Spotify playlist. This tool extracts the titles from the YouTube playlist, searches for the corresponding tracks on Spotify, and creates a new playlist on Spotify with those tracks.

## Features ✨

- Convert a YouTube playlist to a Spotify playlist
- Available as both desktop GUI and web application
- Seamless integration with YouTube and Spotify APIs
- Modern, responsive web interface
- Easy-to-use desktop interface using Tkinter
- Simple and efficient handling of YouTube and Spotify data

## Requirements 📋

Before running this tool, ensure that you have the following installed on your local machine:

- Python 3.x
- pip (Python's package installer)

### Install Required Libraries:

`pip install -r requirements.txt`

## How to Use 🛠️

### Web Application (Recommended for Hosting)

#### 1. Clone the repository:

`git clone https://github.com/lokesh04kaira/playlist-converter.git`

#### 2. Install the necessary dependencies:

`cd playlist-converter`
`pip install -r requirements.txt`

#### 3. Set up your API keys:

You will need a YouTube API key and Spotify API credentials (Client ID and Client Secret).

- Add your API keys in the `config.py` file or set them as environment variables.

#### 4. Run the web application:

`python app.py`

The web application will be available at `http://localhost:5000`

#### 5. Deploy to hosting platforms:

- **Heroku**: Push to Heroku using the provided Procfile
- **Railway**: Connect your GitHub repository
- **Render**: Deploy as a web service
- **Vercel**: Deploy as a Python application

### Desktop Application

#### 1. Run the desktop GUI:

`python main.py`

A window will pop up asking for the YouTube playlist link. Enter the link, and the tool will fetch the playlist and create a new playlist on your Spotify account.

## Hosting Options 🌐

### Heroku Deployment

1. Create a Heroku account
2. Install Heroku CLI
3. Run the following commands:

```bash
heroku create your-app-name
git push heroku main
```

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Python application
3. Set environment variables for API keys

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`

## Environment Variables 🔧

For hosting platforms, set these environment variables:

- `YOUTUBE_API_KEY`: Your YouTube Data API key
- `SPOTIFY_CLIENT_ID`: Your Spotify Client ID
- `SPOTIFY_CLIENT_SECRET`: Your Spotify Client Secret

## Troubleshooting 🛠️

If you encounter any issues while running the tool, consider the following steps:

### 1. API Keys

Ensure that your YouTube API key and Spotify API credentials are correctly added in the `config.py` file or set as environment variables.

### 2. Internet Connection

A stable internet connection is required to connect to both the YouTube and Spotify APIs. Make sure you're connected to the internet.

### 3. Timeout Issues

If you encounter timeout errors, you can try increasing the timeout period in the code or checking the network connectivity.

### 4. Playlist Not Found

If the tool is unable to find tracks in the Spotify search, ensure that the titles in the YouTube playlist match the actual track names as closely as possible. You can also manually edit the playlist titles for better accuracy.

### 5. Hosting Issues

- Ensure all environment variables are set correctly
- Check that the port configuration matches your hosting platform
- Verify that the Spotify redirect URI is updated for your domain

## Project Structure 📁

```
playlist-converter/
├── app.py                 # Flask web application
├── main.py               # Desktop GUI application
├── config.py             # API configuration
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku deployment configuration
├── runtime.txt          # Python version specification
├── templates/           # HTML templates
│   ├── index.html       # Main web interface
│   └── callback.html    # OAuth callback page
└── README.md           # Project documentation
```
