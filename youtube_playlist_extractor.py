import googleapiclient.discovery
import json

api_key = "AIzaSyAUQuKJgcGWZkjZG2MoeE8cxUWRDoqdOTw"
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

playlist_id = "RDMZuYthwMNtg"
request = youtube.playlistItems().list(
    part="snippet",
    playlistId=playlist_id,
    maxResults=50
)

response = request.execute()

playlist_items = []
for item in response['items']:
    title = item['snippet']['title']
    video_id = item['snippet']['resourceId']['videoId']
    playlist_items.append({'title': title, 'video_id': video_id})

# Print the extracted playlist items
print(playlist_items)

with open("youtube_playlist_data.json", "w") as file:
    json.dump(playlist_items, file, indent=4)
