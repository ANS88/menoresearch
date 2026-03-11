import urllib.request
import json
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_posts(subreddit="menopause", category="hot", limit=25):
    url = f"https://www.reddit.com/r/{subreddit}/{category}.json?limit={limit}"
    data = fetch(url)
    posts = data["data"]["children"]
    results = []
    for p in posts:
        d = p["data"]
        results.append({
            "title": d["title"],
            "author": d.get("author", ""),
            "score": d["score"],
            "upvote_ratio": d.get("upvote_ratio", 0),
            "num_comments": d["num_comments"],
            "created_utc": d.get("created_utc", 0),
            "url": "https://reddit.com" + d["permalink"],
            "flair": d.get("link_flair_text", ""),
            "selftext": d.get("selftext", ""),
        })
    return results


def get_comments(permalink, limit=20):
    url = f"https://www.reddit.com{permalink}.json?limit={limit}&depth=2"
    data = fetch(url)
    comments = []
    try:
        for c in data[1]["data"]["children"]:
            if c["kind"] == "t1":
                cd = c["data"]
                comments.append({
                    "author": cd.get("author", ""),
                    "body": cd.get("body", ""),
                    "score": cd.get("score", 0),
                })
    except Exception:
        pass
    return comments


if __name__ == "__main__":
    print("=" * 60)
    print("r/menopause — Top 10 Hot Posts")
    print("=" * 60)

    posts = get_posts(limit=10)
    for i, post in enumerate(posts, 1):
        print(f"\n[{i}] {post['title']}")
        print(f"    Score: {post['score']}  |  Comments: {post['num_comments']}")
        if post["selftext"]:
            print(f"    Preview: {post['selftext'][:150]}...")
        print(f"    URL: {post['url']}")

        # Fetch top comments for first 3 posts
        if i <= 3:
            time.sleep(1)  # be polite to Reddit's servers
            comments = get_comments(post["url"].replace("https://reddit.com", ""))
            if comments:
                print(f"    Top comments:")
                for j, c in enumerate(comments[:3], 1):
                    print(f"      {j}. {c[:150]}")

    print("\n" + "=" * 60)
    print("Done!")
