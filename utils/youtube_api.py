import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_videos(query, max_results=3):
    """Searches YouTube for educational videos matching a topic query.
    Returns a list of dicts: video_id, title, channel, thumbnail."""
    if not API_KEY:
        print("YouTube API key missing - set YOUTUBE_API_KEY in .env")
        return []

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoEmbeddable": "true",
        "relevanceLanguage": "en",
        "maxResults": max_results,
        "key": API_KEY,
    }

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        items = response.json().get("items", [])

        videos = []
        for item in items:
            video_id = item["id"].get("videoId")
            snippet = item["snippet"]
            if not video_id:
                continue
            videos.append({
                "video_id": video_id,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "thumbnail": snippet["thumbnails"]["medium"]["url"],
            })
        return videos

    except Exception as e:
        print(f"YouTube API error: {e}")
        return []
