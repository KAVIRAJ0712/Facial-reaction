import json
import random
from googleapiclient.discovery import build

# Replace with your YouTube Data API key
API_KEY = 'AIzaSyCb-MHnExF3LxHv9N49oUBfGeP-SBQKzSU'

# Initialize the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Define emotion-based queries
queries = {
    "happy": "tamil happy songs",
    "sad": "tamil sad songs",
    "angry": "tamil angry songs",
    "surprise": "tamil surprise songs",
    "neutral": "tamil neutral songs"
}

# Function to fetch video links based on a query
def fetch_video_links(query, max_results=30):
    video_links = []
    next_page_token = None

    while len(video_links) < max_results:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_id = item['id']['videoId']
            video_links.append(f"https://www.youtube.com/watch?v={video_id}")

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return video_links[:max_results]

# Fetch video links for each emotion
emotion_video_links = {}
for emotion, query in queries.items():
    print(f"Fetching videos for emotion: {emotion}")
    emotion_video_links[emotion] = fetch_video_links(query)

# Save the video links to a JSON file
with open('song_links.json', 'w', encoding='utf-8') as f:
    json.dump(emotion_video_links, f, ensure_ascii=False, indent=4)

print("Video links saved to song_links.json")
