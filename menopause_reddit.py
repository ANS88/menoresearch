import urllib.request
import urllib.parse
import json
import time
import os
import base64

CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
USER_AGENT = "menopause-research/2.0 by research-app"

_token_cache = {"token": None, "expires": 0}


def _get_token():
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {creds}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    _token_cache["token"] = data["access_token"]
    _token_cache["expires"] = time.time() + data["expires_in"] - 60
    return _token_cache["token"]


def fetch(url):
    if CLIENT_ID and CLIENT_SECRET:
        token = _get_token()
        oauth_url = url.replace("https://www.reddit.com", "https://oauth.reddit.com")
        req = urllib.request.Request(
            oauth_url,
            headers={"Authorization": f"bearer {token}", "User-Agent": USER_AGENT},
        )
    else:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT},
        )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def _parse_posts(children):
    results = []
    for p in children:
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


def get_posts(subreddit="menopause", category="hot", limit=25):
    url = f"https://www.reddit.com/r/{subreddit}/{category}.json?limit={min(limit, 100)}"
    data = fetch(url)
    return _parse_posts(data["data"]["children"])[:limit]


def get_all_posts(subreddit="menopause", category="hot", max_pages=10, time_filter=None):
    """Paginate through up to max_pages * 100 posts."""
    results = []
    after = None
    for _ in range(max_pages):
        url = f"https://www.reddit.com/r/{subreddit}/{category}.json?limit=100"
        if time_filter:
            url += f"&t={time_filter}"
        if after:
            url += f"&after={after}"
        data = fetch(url)
        page = data["data"]["children"]
        if not page:
            break
        results.extend(_parse_posts(page))
        after = data["data"].get("after")
        if not after:
            break
        time.sleep(0.6)  # stay within Reddit's rate limit
    return results


def _parse_comment(cd):
    return {
        "author": cd.get("author", ""),
        "body": cd.get("body", ""),
        "score": cd.get("score", 0),
    }


def get_comments(permalink, limit=500):
    """Fetch all top-level comments for a post, following 'more' links."""
    url = f"https://www.reddit.com{permalink}.json?limit={limit}&depth=1"
    data = fetch(url)

    comments = []
    more_ids = []
    link_id = None

    try:
        link_id = data[0]["data"]["children"][0]["data"]["name"]  # e.g. t3_abc123
        for c in data[1]["data"]["children"]:
            if c["kind"] == "t1":
                comments.append(_parse_comment(c["data"]))
            elif c["kind"] == "more":
                more_ids.extend(c["data"].get("children", []))
    except Exception:
        pass

    # Follow 'more' links in batches of 100 to get remaining comments
    if link_id and more_ids:
        batch_size = 100
        for i in range(0, len(more_ids), batch_size):
            batch = ",".join(more_ids[i:i + batch_size])
            try:
                mc_url = (
                    f"https://www.reddit.com/api/morechildren.json"
                    f"?api_type=json&link_id={link_id}&children={batch}&depth=1"
                )
                mc_data = fetch(mc_url)
                for item in mc_data.get("json", {}).get("data", {}).get("things", []):
                    if item["kind"] == "t1":
                        cd = item["data"]
                        # top-level only: parent is the post itself
                        if cd.get("parent_id") == link_id:
                            comments.append(_parse_comment(cd))
                time.sleep(0.5)
            except Exception:
                break

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

        if i <= 3:
            time.sleep(1)
            comments = get_comments(post["url"].replace("https://reddit.com", ""))
            if comments:
                print(f"    Top comments:")
                for j, c in enumerate(comments[:3], 1):
                    print(f"      {j}. {c['body'][:150]}")

    print("\n" + "=" * 60)
    print("Done!")
