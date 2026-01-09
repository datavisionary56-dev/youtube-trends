import os
import requests
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

COUNTRY = "SA"
MAX_RESULTS = 10

def fetch_trending_videos():
    print("Fetching YouTube trending videos...")
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": COUNTRY,
        "maxResults": MAX_RESULTS,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["items"]

def save_to_supabase(videos):
    print("Saving to Supabase...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    rows = []
    for v in videos:
        rows.append({
            "platform": "youtube",
            "country": COUNTRY,
            "video_id": v["id"],
            "title": v["snippet"]["title"],
            "channel_title": v["snippet"]["channelTitle"],
            "published_at": v["snippet"]["publishedAt"],
            "view_count": int(v["statistics"].get("viewCount", 0)),
            "like_count": int(v["statistics"].get("likeCount", 0)),
            "comment_count": int(v["statistics"].get("commentCount", 0)),
            "thumbnail_url": v["snippet"]["thumbnails"]["high"]["url"],
            "video_url": f"https://www.youtube.com/watch?v={v['id']}",
            "fetched_at": datetime.utcnow().isoformat()
        })

    endpoint = f"{SUPABASE_URL}/rest/v1/trends"
    r = requests.post(endpoint, json=rows, headers=headers)
    r.raise_for_status()

def main():
    print("=== SCRIPT STARTED ===")
    videos = fetch_trending_videos()
    print(f"Fetched {len(videos)} videos")
    save_to_supabase(videos)
    print("=== DONE ===")

if __name__ == "__main__":
    main()
