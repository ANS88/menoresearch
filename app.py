import re
from collections import Counter
from flask import Flask, jsonify, render_template, request
from menopause_reddit import get_posts, get_comments, fetch

app = Flask(__name__)

MOCK_POSTS = [
    {
        "title": "Finally feeling like myself again after starting HRT",
        "score": 1842,
        "num_comments": 214,
        "url": "https://reddit.com/r/menopause/comments/example1/",
        "selftext": "I was skeptical at first but three months in and the brain fog has lifted, night sweats are gone, and I actually slept through the night for the first time in two years. Sharing in case it helps someone on the fence."
    },
    {
        "title": "What symptoms hit you first? Looking for others' experiences",
        "score": 976,
        "num_comments": 389,
        "url": "https://reddit.com/r/menopause/comments/example2/",
        "selftext": "For me it started with irregular periods and then the insomnia crept in. Hot flashes came later. Curious if others had a similar progression or something totally different."
    },
    {
        "title": "Magnesium glycinate changed my sleep — anyone else?",
        "score": 743,
        "num_comments": 167,
        "url": "https://reddit.com/r/menopause/comments/example3/",
        "selftext": "Started 400 mg magnesium glycinate at night two weeks ago. I'm not exaggerating when I say it's been life changing for sleep. Doctor approved. Just wanted to share."
    },
    {
        "title": "Brain fog is real and nobody warned me",
        "score": 618,
        "num_comments": 201,
        "url": "https://reddit.com/r/menopause/comments/example4/",
        "selftext": "I'm a lawyer and I kept forgetting words mid-sentence. Thought I was developing early dementia. Turns out it's perimenopause. Why isn't this talked about more?"
    },
    {
        "title": "Non-hormonal options that actually helped — my list after 2 years",
        "score": 534,
        "num_comments": 143,
        "url": "https://reddit.com/r/menopause/comments/example5/",
        "selftext": "Can't do HRT due to personal history. Here's what helped: magnesium, ashwagandha, cold room at night, weighted blanket, and cutting alcohol entirely."
    },
    {
        "title": "Doctors dismissing symptoms — anyone else fighting for care?",
        "score": 491,
        "num_comments": 298,
        "url": "https://reddit.com/r/menopause/comments/example6/",
        "selftext": "Third doctor told me I'm 'too young' at 46. My bloodwork says otherwise. Looking for advice on finding a menopause specialist."
    },
    {
        "title": "Vaginal dryness — let's talk about it openly",
        "score": 412,
        "num_comments": 176,
        "url": "https://reddit.com/r/menopause/comments/example7/",
        "selftext": "Nobody warned me about this. Local estrogen cream helped enormously and it's low risk. Please don't suffer in silence like I did for a year."
    },
    {
        "title": "Weekly support thread — how are you doing this week?",
        "score": 387,
        "num_comments": 524,
        "url": "https://reddit.com/r/menopause/comments/example8/",
        "selftext": "Share how your week went, wins, struggles, questions. We're all in this together."
    },
    {
        "title": "Exercise actually helped my hot flashes — here's what I do",
        "score": 354,
        "num_comments": 89,
        "url": "https://reddit.com/r/menopause/comments/example9/",
        "selftext": "30 min of strength training 4x per week. Hot flashes reduced by about 60% after 6 weeks. I know it doesn't work for everyone but worth trying."
    },
    {
        "title": "Joint pain and menopause — the connection nobody explains",
        "score": 311,
        "num_comments": 132,
        "url": "https://reddit.com/r/menopause/comments/example10/",
        "selftext": "I thought I was just getting old. Turns out dropping estrogen causes widespread joint inflammation. My rheumatologist finally connected the dots."
    },
]

MOCK_COMMENTS = {
    "example1": [
        "Same experience here. The difference was night and day within 6 weeks. Stick with it.",
        "What type of HRT are you on? Patch or pills? I'm just starting the conversation with my doctor.",
        "This gives me hope. I've been putting it off because I was scared of the risks but my quality of life is so bad right now.",
        "The brain fog lifting was the biggest thing for me too. I felt like I got my personality back.",
        "Thank you for sharing this. I cried reading it because I thought I'd just have to accept feeling terrible forever.",
    ],
    "example2": [
        "For me it was insomnia first, way before any period changes. Two years of bad sleep before anyone suggested perimenopause.",
        "Mine started with anxiety out of nowhere. I'd never had anxiety in my life. Took 18 months to figure out what was happening.",
        "Heart palpitations were my first sign. Terrifying until I found out it was hormonal.",
        "Irregular cycles then rage. Like disproportionate, sudden rage. My family thought I was losing it.",
    ],
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/posts")
def api_posts():
    category = request.args.get("category", "hot")
    limit = int(request.args.get("limit", 25))
    try:
        posts = get_posts(category=category, limit=limit)
        return jsonify({"ok": True, "posts": posts, "source": "live"})
    except Exception as e:
        # Fall back to mock data if Reddit is unreachable
        posts = MOCK_POSTS[:limit]
        return jsonify({"ok": True, "posts": posts, "source": "mock", "warning": str(e)})


@app.route("/api/comments")
def api_comments():
    permalink = request.args.get("permalink", "")
    if not permalink:
        return jsonify({"ok": False, "error": "permalink required"}), 400
    try:
        comments = get_comments(permalink, limit=10)
        if comments:
            return jsonify({"ok": True, "comments": comments, "source": "live"})
        raise ValueError("no comments returned")
    except Exception as e:
        # Fall back to mock comments
        key = next((k for k in MOCK_COMMENTS if k in permalink), None)
        raw = MOCK_COMMENTS.get(key, [
            "This is a great question. I had a similar experience and found that talking to a menopause specialist rather than a GP made all the difference.",
            "Thank you for bringing this up. So many of us deal with this silently.",
            "I recommend checking out the wiki in this subreddit — there's a lot of helpful information compiled there.",
        ])
        comments = [{"author": "redditor", "body": c, "score": 0} for c in raw]
        return jsonify({"ok": True, "comments": comments, "source": "mock", "warning": str(e)})


STOPWORDS = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they", "it",
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "was", "are", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "not", "no", "so", "if", "just", "like", "that", "this", "what", "how",
    "from", "about", "up", "out", "get", "got", "can", "all", "more", "also",
    "than", "then", "when", "there", "their", "them", "who", "which", "after",
    "before", "been", "its", "any", "some", "as", "well", "one", "know",
    "think", "really", "ve", "ll", "re", "m", "s", "t", "d", "amp",
}


def extract_keywords(posts, top_n=30):
    words = []
    for p in posts:
        text = p.get("title", "") + " " + p.get("selftext", "")
        tokens = re.findall(r"[a-z]{3,}", text.lower())
        words.extend(t for t in tokens if t not in STOPWORDS)
    counts = Counter(words)
    return [{"word": w, "count": c} for w, c in counts.most_common(top_n)]


@app.route("/api/keywords")
def api_keywords():
    category = request.args.get("category", "hot")
    limit = int(request.args.get("limit", 50))
    top_n = int(request.args.get("top", 30))
    try:
        posts = get_posts(category=category, limit=limit)
        source = "live"
    except Exception:
        posts = MOCK_POSTS
        source = "mock"
    keywords = extract_keywords(posts, top_n=top_n)
    return jsonify({"ok": True, "keywords": keywords, "source": source})


@app.route("/api/stats")
def api_stats():
    try:
        data = fetch("https://www.reddit.com/r/menopause/about.json")
        d = data["data"]
        return jsonify({
            "ok": True,
            "subscribers": d.get("subscribers", 0),
            "active": d.get("active_user_count", 0),
            "created_utc": d.get("created_utc", 0),
            "title": d.get("title", ""),
            "source": "live",
        })
    except Exception as e:
        return jsonify({
            "ok": True,
            "subscribers": 172000,
            "active": 312,
            "created_utc": 1279152000,
            "title": "Menopause",
            "source": "mock",
            "warning": str(e),
        })


def _pearson(x, y):
    """Pearson r between two equal-length lists. Returns 0 if constant."""
    n = len(x)
    if n < 2:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = sum((xi - mx) ** 2 for xi in x) ** 0.5
    dy = sum((yi - my) ** 2 for yi in y) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


@app.route("/api/correlation")
def api_correlation():
    category = request.args.get("category", "hot")
    limit = int(request.args.get("limit", 50))
    top_n = int(request.args.get("top", 20))
    try:
        posts = get_posts(category=category, limit=limit)
        source = "live"
    except Exception:
        posts = MOCK_POSTS
        source = "mock"

    # Collect all words to find top keywords
    all_words = []
    for p in posts:
        text = p.get("title", "") + " " + p.get("selftext", "")
        tokens = re.findall(r"[a-z]{3,}", text.lower())
        all_words.extend(t for t in tokens if t not in STOPWORDS)

    top_keywords = [w for w, _ in Counter(all_words).most_common(top_n)]

    # Build per-post frequency vectors (one count per keyword per post)
    freq_matrix = []  # shape: [num_posts][num_keywords]
    for p in posts:
        text = p.get("title", "") + " " + p.get("selftext", "")
        counts_p = Counter(re.findall(r"[a-z]{3,}", text.lower()))
        freq_matrix.append([counts_p.get(kw, 0) for kw in top_keywords])

    n = len(top_keywords)

    # Pearson correlation matrix between keyword frequency vectors
    corr = [[0.0] * n for _ in range(n)]
    for i in range(n):
        corr[i][i] = 1.0
        col_i = [freq_matrix[r][i] for r in range(len(freq_matrix))]
        for j in range(i + 1, n):
            col_j = [freq_matrix[r][j] for r in range(len(freq_matrix))]
            r = round(_pearson(col_i, col_j), 3)
            corr[i][j] = r
            corr[j][i] = r

    # Sorted pairs by absolute Pearson r (strongest first)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            r = corr[i][j]
            if r != 0.0:
                pairs.append({
                    "word_a": top_keywords[i],
                    "word_b": top_keywords[j],
                    "r": r,
                })
    pairs.sort(key=lambda x: abs(x["r"]), reverse=True)

    return jsonify({
        "ok": True,
        "keywords": top_keywords,
        "matrix": corr,
        "pairs": pairs[:50],
        "source": source,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
