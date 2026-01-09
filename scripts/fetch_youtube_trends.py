import os
import requests
from datetime import datetime

# ====== Environment variables (GitHub Secrets) ======
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # Service Role Key
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# ====== Settings ======
COUNTRY = "SA"        # مثال: SA, EG, US, AE ...
MAX_RESULTS = 10


def fetch_trending_videos():
    if not YOUTUBE_API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY")

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

    data = r.json()
    items = data.get("items", [])
    return items


def save_to_supabase(videos):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing Supabase credentials (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        # merge-duplicates = Upsert behavior
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    rows = []

    for video in videos:
        vid = video.get("id")
        snippet = video.get("snippet", {}) or {}
        stats = video.get("statistics", {}) or {}

        rows.append({
            "platform": "youtube",
            "country": COUNTRY,
            "video_id": vid,
            "title": snippet.get("title"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "thumbnail_url": (snippet.get("thumbnails", {}) or {}).get("high", {}).get("url"),
            "video_url": f"https://www.youtube.com/watch?v={vid}",
            "view_count": int(stats.get("viewCount", 0) or 0),
            "like_count": int(stats.get("likeCount", 0) or 0),
            "comment_count": int(stats.get("commentCount", 0) or 0),
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        })

    endpoint = f"{SUPABASE_URL}/rest/v1/trends"

    # on_conflict يعمل upsert حسب video_id (لازم يكون عندك UNIQUE على video_id في الجدول)
    params = {"on_conflict": "video_id"}

    r = requests.post(endpoint, headers=headers, params=params, json=rows, timeout=60)

    if not r.ok:
        print("Supabase error status:", r.status_code)
        print("Supabase response:", r.text)
        r.raise_for_status()

    try:
        inserted = r.json()
        print(f"Inserted/Upserted rows: {len(inserted)}")
    except Exception:
        # لو رجع نص مش JSON
        print("Supabase response:", r.text)
        print("Saved to Supabase (response not JSON).")


def main():
    print("=== SCRIPT STARTED ===")
    print("Fetching YouTube trending videos...")

    videos = fetch_trending_videos()
    print(f"Fetched {len(videos)} videos")

    print("Saving to Supabase...")
    save_to_supabase(videos)

    print("=== DONE ✅ ===")


if __name__ == "__main__":
    main()
