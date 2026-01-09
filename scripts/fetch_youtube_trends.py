import os
import requests
from datetime import datetime

# Environment variables (من GitHub Secrets)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# إعدادات
COUNTRY = "SA"   # غيرها لو حابب: EG, US, AE ...
MAX_RESULTS = 10


def fetch_trending_videos():
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": COUNTRY,
        "maxResults": MAX_RESULTS,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["items"]


def save_to_supabase(videos):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    rows = []
    for video in videos:
        rows.append({
            "platform": "youtube",
            "country": COUNTRY,
            "video_id": video["id"],
            "title": video["snippet"]["title"],
            "channel_title": video["snippet"]["channelTitle"],
            "published_at": video["snippet"]["publishedAt"],
            "views": int(video["statistics"].get("viewCount", 0)),
            "likes": int(video["statistics"].get("likeCount", 0)),
            "comments": int(video["statistics"].get("commentCount", 0)),
            "fetched_at": datetime.utcnow().isoformat()
        })

    supabase_endpoint = f"{SUPABASE_URL}/rest/v1/trends"
    r = requests.post(supabase_endpoint, json=rows, headers=headers, timeout=30)
    r.raise_for_status()


def main():
    print("Fetching YouTube trending videos...")
    videos = fetch_trending_videos()
    print(f"Fetched {len(videos)} videos")

    print("Saving to Supabase...")
    save_to_supabase(videos)
    print("Done ✅")


if __name__ == "__main__":
    main()
