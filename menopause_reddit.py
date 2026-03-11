import urllib.request
import json
import time

HEADERS = {"User-Agent": "menopause-research/1.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_posts(subreddit="menopause", category="hot", limit=10):
    url = f"https://www.reddit.com/r/{subreddit}/{category}.json?limit={limit}"
    data = fetch(url)
    posts = data["data"]["children"]
    results = []
    for p in posts:
        d = p["data"]
        results.append({
            "title": d["title"],
            "score": d["score"],
            "num_comments": d["num_comments"],
            "url": "https://reddit.com" + d["permalink"],
            "selftext": d.get("selftext", "")[:300]  # first 300 chars
        })
    return results


def get_comments(permalink, limit=5):
    url = f"https://www.reddit.com{permalink}.json?limit={limit}"
    data = fetch(url)
    comments = []
    try:
        for c in data[1]["data"]["children"]:
            if c["kind"] == "t1":
                comments.append(c["data"]["body"][:300])
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
