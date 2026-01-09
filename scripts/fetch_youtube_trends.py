def save_to_supabase(videos):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        # مهم للـ upsert مع unique index
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    rows = []
    for video in videos:
        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})

        rows.append({
            "platform": "youtube",
            "country": COUNTRY,
            "video_id": video.get("id"),
            "title": snippet.get("title"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),  # YouTube RFC3339
            "views": int(stats.get("viewCount", 0) or 0),
            "likes": int(stats.get("likeCount", 0) or 0),
            "comments": int(stats.get("commentCount", 0) or 0),
            "fetched_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        })

    # ✅ upsert باستخدام الـ unique index اللي عندك (platform,country,video_id)
    supabase_endpoint = f"{SUPABASE_URL}/rest/v1/trends?on_conflict=platform,country,video_id"

    r = requests.post(supabase_endpoint, json=rows, headers=headers, timeout=30)

    # ✅ اطبع سبب الخطأ الحقيقي لو حصل 400/401/...
    if r.status_code >= 300:
        print("Supabase status:", r.status_code)
        print("Supabase response:", r.text)
        r.raise_for_status()

    print("Saved to Supabase OK ✅")
