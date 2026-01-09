import os
import requests
from datetime import datetime

# Env vars (GitHub Secrets)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()  # مهم: نفس اسم السيكرت في الـ workflow
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

# Settings
COUNTRY = "SA"
MAX_RESULTS = 10

def fetch_trending_videos():
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": COUNTRY,
        "maxResults": MAX_RESULTS,
        "key": YOUTUBE_API_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])

def save_to_supabase(videos):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    if not YOUTUBE_API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY")

    endpoint = f"{SUPABASE_URL.rstrip('/')}/rest/v1/trends"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    rows = []
    for v in videos:
        snippet = v.get("snippet", {}) or {}
        stats = v.get("statistics", {}) or {}

        video_id = v.get("id")
        if not video_id:
            continue

        rows.append({
            "platform": "youtube",
            "country": COUNTRY,
            "video_id": video_id,
            "title": snippet.get("title"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "thumbnail_url": (snippet.get("thumbnails", {}) or {}).get("high", {}).get("url"),
            "video_url": f"https://www.youtube.com/watch?v={video_id}",

            # ✅ مهم: نفس أسماء الأعمدة الموجودة في جدولك
            "view_count": int(stats.get("viewCount", 0) or 0),
            "likes": int(stats.get("likeCount", 0) or 0),
            "comments": int(stats.get("commentCount", 0) or 0),

            "fetched_at": datetime.utcnow().isoformat()
        })

    # لو جدولك فيه UNIQUE على video_id، ده يخلي الـ upsert يشتغل صح
    params = {"on_conflict": "video_id"}

    r = requests.post(endpoint, params=params, json=rows, headers=headers, timeout=60)

    if not r.ok:
        print("Supabase status:", r.status_code)
        print("Supabase response:", r.text)
        r.raise_for_status()

def main():
    print("SCRIPT STARTED")
    videos = fetch_trending_videos()
    print(f"Fetched {len(videos)} videos")
    print("Saving to Supabase")
    save_to_supabase(videos)
    print("DONE")

if __name__ == "__main__":
    main()
