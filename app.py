import re
from collections import Counter
from flask import Flask, jsonify, render_template, request
from menopause_reddit import get_posts, get_all_posts, get_comments, fetch

app = Flask(__name__)

# Timestamps: 10 posts spread ~8 days apart ending ~2026-03-10
_T = [1773100800, 1772410000, 1771720000, 1771030000, 1770340000,
      1769650000, 1768960000, 1768270000, 1767580000, 1766890000]

MOCK_POSTS = [
    {
        "title": "Finally feeling like myself again after starting HRT",
        "score": 1842, "num_comments": 214, "created_utc": _T[0],
        "upvote_ratio": 0.97, "author": "hopeful_user",
        "url": "https://reddit.com/r/menopause/comments/example1/",
        "selftext": "I was skeptical at first but three months in and the brain fog has lifted, night sweats are gone, and I actually slept through the night for the first time in two years. Sharing in case it helps someone on the fence."
    },
    {
        "title": "What symptoms hit you first? Looking for others' experiences",
        "score": 976, "num_comments": 389, "created_utc": _T[1],
        "upvote_ratio": 0.95, "author": "curious_perimenopause",
        "url": "https://reddit.com/r/menopause/comments/example2/",
        "selftext": "For me it started with irregular periods and then the insomnia crept in. Hot flashes came later. Curious if others had a similar progression or something totally different."
    },
    {
        "title": "Magnesium glycinate changed my sleep — anyone else?",
        "score": 743, "num_comments": 167, "created_utc": _T[2],
        "upvote_ratio": 0.96, "author": "sleep_seeker",
        "url": "https://reddit.com/r/menopause/comments/example3/",
        "selftext": "Started 400 mg magnesium glycinate at night two weeks ago. I'm not exaggerating when I say it's been life changing for sleep. Doctor approved. Just wanted to share."
    },
    {
        "title": "Brain fog is real and nobody warned me",
        "score": 618, "num_comments": 201, "created_utc": _T[3],
        "upvote_ratio": 0.98, "author": "foggy_lawyer",
        "url": "https://reddit.com/r/menopause/comments/example4/",
        "selftext": "I'm a lawyer and I kept forgetting words mid-sentence. Thought I was developing early dementia. Turns out it's perimenopause. Why isn't this talked about more?"
    },
    {
        "title": "Non-hormonal options that actually helped — my list after 2 years",
        "score": 534, "num_comments": 143, "created_utc": _T[4],
        "upvote_ratio": 0.94, "author": "natural_path",
        "url": "https://reddit.com/r/menopause/comments/example5/",
        "selftext": "Can't do HRT due to personal history. Here's what helped: magnesium, ashwagandha, cold room at night, weighted blanket, and cutting alcohol entirely."
    },
    {
        "title": "Doctors dismissing symptoms — anyone else fighting for care?",
        "score": 491, "num_comments": 298, "created_utc": _T[5],
        "upvote_ratio": 0.93, "author": "advocate46",
        "url": "https://reddit.com/r/menopause/comments/example6/",
        "selftext": "Third doctor told me I'm 'too young' at 46. My bloodwork says otherwise. Looking for advice on finding a menopause specialist."
    },
    {
        "title": "Vaginal dryness — let's talk about it openly",
        "score": 412, "num_comments": 176, "created_utc": _T[6],
        "upvote_ratio": 0.96, "author": "open_talk",
        "url": "https://reddit.com/r/menopause/comments/example7/",
        "selftext": "Nobody warned me about this. Local estrogen cream helped enormously and it's low risk. Please don't suffer in silence like I did for a year."
    },
    {
        "title": "Weekly support thread — how are you doing this week?",
        "score": 387, "num_comments": 524, "created_utc": _T[7],
        "upvote_ratio": 0.91, "author": "mod_team",
        "url": "https://reddit.com/r/menopause/comments/example8/",
        "selftext": "Share how your week went, wins, struggles, questions. We're all in this together."
    },
    {
        "title": "Exercise actually helped my hot flashes — here's what I do",
        "score": 354, "num_comments": 89, "created_utc": _T[8],
        "upvote_ratio": 0.95, "author": "fitness_meno",
        "url": "https://reddit.com/r/menopause/comments/example9/",
        "selftext": "30 min of strength training 4x per week. Hot flashes reduced by about 60% after 6 weeks. I know it doesn't work for everyone but worth trying."
    },
    {
        "title": "Joint pain and menopause — the connection nobody explains",
        "score": 311, "num_comments": 132, "created_utc": _T[9],
        "upvote_ratio": 0.94, "author": "joint_discovery",
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


SYMPTOMS = {
    "hot flashes":        ["hot flash", "hot flashes", "hot flush", "hot flushes"],
    "night sweats":       ["night sweat", "night sweats"],
    "brain fog":          ["brain fog", "brain fogg", "foggy brain", "mental fog"],
    "insomnia":           ["insomnia", "can't sleep", "cannot sleep", "trouble sleeping",
                           "sleep problem", "sleep issues", "sleep disturbance", "not sleeping"],
    "anxiety":            ["anxiety", "anxious", "panic attack", "panic attacks"],
    "depression":         ["depression", "depressed", "low mood"],
    "mood swings":        ["mood swing", "mood swings", "mood change", "mood changes",
                           "irritab", "irritability"],
    "fatigue":            ["fatigue", "exhaustion", "exhausted", "tired all the time",
                           "chronic fatigue", "low energy"],
    "joint pain":         ["joint pain", "joint ache", "achy joints", "joint inflammation",
                           "joint stiffness", "arthritis"],
    "vaginal dryness":    ["vaginal dryness", "vaginal atrophy", "dryness", "painful sex",
                           "dyspareunia"],
    "irregular periods":  ["irregular period", "irregular cycle", "missed period",
                           "skipped period", "heavy period", "heavy bleeding", "spotting"],
    "weight gain":        ["weight gain", "gaining weight", "gained weight", "belly fat",
                           "abdominal weight", "metabolism"],
    "heart palpitations": ["heart palpitation", "heart palpitations", "palpitation",
                           "racing heart", "heart racing", "irregular heartbeat"],
    "headaches":          ["headache", "headaches", "migraine", "migraines"],
    "memory loss":        ["memory loss", "memory problem", "forgetful", "forgetting words",
                           "word recall", "cognitive"],
    "low libido":         ["low libido", "loss of libido", "low sex drive", "no sex drive",
                           "loss of interest in sex"],
    "skin changes":       ["skin change", "dry skin", "itchy skin", "skin itch", "crawling skin",
                           "formication"],
    "hair loss":          ["hair loss", "hair thinning", "losing hair", "thinning hair"],
    "bloating":           ["bloating", "bloated", "digestive", "gut issue"],
    "urinary issues":     ["urinary", "bladder", "incontinence", "uti", "frequent urination",
                           "overactive bladder"],
}


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


@app.route("/api/symptoms")
def api_symptoms():
    category = request.args.get("category", "hot")
    max_pages = int(request.args.get("pages", 5))
    try:
        posts = get_all_posts(category=category, max_pages=max_pages)
        source = "live"
    except Exception:
        posts = MOCK_POSTS
        source = "mock"

    counts = {symptom: 0 for symptom in SYMPTOMS}
    post_counts = {symptom: 0 for symptom in SYMPTOMS}  # posts mentioning it at least once

    for p in posts:
        text = (p.get("title", "") + " " + p.get("selftext", "")).lower()
        for symptom, patterns in SYMPTOMS.items():
            hits = sum(text.count(pat) for pat in patterns)
            counts[symptom] += hits
            if hits > 0:
                post_counts[symptom] += 1

    results = [
        {"symptom": s, "mentions": counts[s], "posts": post_counts[s]}
        for s in SYMPTOMS if counts[s] > 0
    ]
    results.sort(key=lambda x: x["mentions"], reverse=True)

    return jsonify({"ok": True, "symptoms": results, "total_posts": len(posts), "source": source})


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


POST_CATEGORIES = [
    {
        "id": "hrt",
        "label": "HRT & Hormone Therapy",
        "patterns": [
            "hrt", "hormone therapy", "hormone replacement", "estrogen", "estradiol",
            "progesterone", "progestin", "testosterone", "bioidentical", "vivelle",
            "prometrium", "provera", "norethindrone", "patch", "pellet",
        ],
    },
    {
        "id": "symptoms",
        "label": "Symptom Identification",
        "patterns": [
            "hot flash", "hot flush", "night sweat", "hot flashes", "hot flushes",
            "palpitation", "racing heart", "dizzy", "dizziness", "tingling",
            "formication", "crawling skin", "symptom",
        ],
    },
    {
        "id": "nonhormonal",
        "label": "Non-Hormonal Treatments",
        "patterns": [
            "magnesium", "ashwagandha", "black cohosh", "evening primrose",
            "supplement", "vitamin", "herbal", "natural remedy", "lifestyle",
            "exercise", "strength training", "yoga", "meditation", "acupuncture",
            "weighted blanket", "cut alcohol", "diet change",
        ],
    },
    {
        "id": "mental",
        "label": "Mental & Cognitive Health",
        "patterns": [
            "brain fog", "anxiety", "anxious", "depression", "depressed",
            "mood swing", "mood change", "irritab", "rage", "anger",
            "panic attack", "panic", "memory", "forget", "cognitive",
            "tearful", "crying", "low mood", "mental health",
        ],
    },
    {
        "id": "medical",
        "label": "Medical Access & Care",
        "patterns": [
            "doctor", "physician", "gp", "gynecologist", "specialist",
            "dismissed", "too young", "bloodwork", "blood test", "fsh", "lh",
            "diagnosis", "menopause specialist", "obgyn", "ob/gyn",
            "appointment", "prescribed", "prescription",
        ],
    },
    {
        "id": "sleep",
        "label": "Sleep",
        "patterns": [
            "sleep", "insomnia", "awake at", "wake up", "waking up",
            "restless", "sleepless", "can't sleep", "cannot sleep",
            "sleep problem", "sleep issue",
        ],
    },
    {
        "id": "sexual",
        "label": "Sexual Health & Relationships",
        "patterns": [
            "vaginal dryness", "vaginal atrophy", "libido", "sex drive",
            "painful sex", "dyspareunia", "intimacy", "relationship", "partner",
            "husband", "local estrogen", "gsm", "genitourinary",
        ],
    },
    {
        "id": "body",
        "label": "Body Changes",
        "patterns": [
            "weight gain", "gaining weight", "hair loss", "losing hair",
            "thinning hair", "skin change", "dry skin", "itchy skin",
            "bloat", "belly fat", "metabolism", "joint pain", "joint ache",
        ],
    },
    {
        "id": "perimenopause",
        "label": "Perimenopause & Transition",
        "patterns": [
            "perimenopause", "perimenopausal", "peri-menopause",
            "irregular period", "irregular cycle", "skipped period",
            "missed period", "still having period", "transition",
        ],
    },
    {
        "id": "support",
        "label": "Community Support & Shared Experience",
        "patterns": [
            "anyone else", "not alone", "feeling alone", "thank you",
            "support thread", "weekly thread", "sharing", "vent",
            "grateful", "hope", "solidarity", "me too",
        ],
    },
]


@app.route("/api/top-posts")
def api_top_posts():
    """Fetch all-time top posts from r/menopause via the backend (avoids browser CORS/rate-limit issues)."""
    try:
        posts = get_all_posts(category="top", time_filter="all", max_pages=10)
        return jsonify({"ok": True, "posts": posts})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502


@app.route("/api/analyze-comments")
def api_analyze_comments():
    """
    For each topic category, fetch comments from the top posts in that category
    and return the 10 highest-upvoted comments per category.

    Query params:
      pages     - how many pages of top posts to fetch (default 3, max 10)
      posts_per_cat - how many top posts per category to pull comments from (default 3)
      comments_per_post - comments fetched per post (default 20)
    """
    try:
        pages = min(int(request.args.get("pages", 3)), 10)
        posts_per_cat = min(int(request.args.get("posts_per_cat", 3)), 10)
        comments_per_post = min(int(request.args.get("comments_per_post", 20)), 100)
    except ValueError:
        return jsonify({"ok": False, "error": "invalid query params"}), 400

    try:
        all_posts = get_all_posts(category="top", time_filter="all", max_pages=pages)
    except Exception as e:
        return jsonify({"ok": False, "error": f"could not fetch posts: {e}"}), 502

    # Categorise every post
    def match_categories(p):
        text = (p.get("title", "") + " " + p.get("selftext", "")).lower()
        matched = []
        for cat in POST_CATEGORIES:
            hits = sum(text.count(pat) for pat in cat["patterns"])
            if hits > 0:
                matched.append((cat["id"], hits))
        return matched

    # Build per-category post lists sorted by score
    cat_posts = {cat["id"]: [] for cat in POST_CATEGORIES}
    for p in all_posts:
        for cat_id, hits in match_categories(p):
            cat_posts[cat_id].append((p["score"], hits, p))
    for cat_id in cat_posts:
        cat_posts[cat_id].sort(key=lambda x: x[0], reverse=True)

    results = []
    seen_permalinks = set()  # avoid fetching the same post twice across categories

    for cat in POST_CATEGORIES:
        cat_id = cat["id"]
        top_posts = [p for _, _, p in cat_posts[cat_id][:posts_per_cat]]
        all_comments = []

        for p in top_posts:
            permalink = p["url"].replace("https://reddit.com", "")
            if permalink in seen_permalinks:
                # still include previously fetched comments stored on the post
                continue
            seen_permalinks.add(permalink)
            try:
                comments = get_comments(permalink, limit=comments_per_post)
                for c in comments:
                    c["post_title"] = p["title"]
                    c["post_url"] = p["url"]
                all_comments.extend(comments)
            except Exception:
                pass

        # Sort by score, take top 10
        top_comments = sorted(all_comments, key=lambda c: c.get("score", 0), reverse=True)[:10]

        results.append({
            "id": cat_id,
            "label": cat["label"],
            "post_count": len(top_posts),
            "top_comments": top_comments,
        })

    return jsonify({"ok": True, "categories": results, "total_posts_fetched": len(all_posts)})


@app.route("/api/categorize", methods=["POST"])
def api_categorize():
    """Assign posts to topic categories based on keyword matching."""
    body = request.get_json(force=True, silent=True) or {}
    posts = body.get("posts", [])
    if not posts:
        return jsonify({"ok": False, "error": "no posts provided"}), 400

    results = []
    for cat in POST_CATEGORIES:
        matched = []
        total_hits = 0
        for p in posts:
            text = (p.get("title", "") + " " + p.get("selftext", "")).lower()
            hits = sum(text.count(pat) for pat in cat["patterns"])
            if hits > 0:
                matched.append((hits, p))
                total_hits += hits
        matched.sort(key=lambda x: (x[0], x[1].get("score", 0)), reverse=True)
        results.append({
            "id": cat["id"],
            "label": cat["label"],
            "count": len(matched),
            "total_hits": total_hits,
            "posts": [p for _, p in matched[:25]],
        })

    results.sort(key=lambda x: x["count"], reverse=True)
    return jsonify({"ok": True, "categories": results, "total_posts": len(posts)})


@app.route("/api/cooccurrence", methods=["POST"])
def api_cooccurrence():
    """Return a co-occurrence matrix: how many posts match each pair of categories."""
    body = request.get_json(force=True, silent=True) or {}
    posts = body.get("posts", [])
    if not posts:
        return jsonify({"ok": False, "error": "no posts provided"}), 400

    ids     = [c["id"]    for c in POST_CATEGORIES]
    labels  = [c["label"] for c in POST_CATEGORIES]
    patterns = [c["patterns"] for c in POST_CATEGORIES]
    n = len(ids)

    # matched[i] = set of post indices that match category i
    matched = [set() for _ in range(n)]
    for idx, p in enumerate(posts):
        text = (p.get("title", "") + " " + p.get("selftext", "")).lower()
        for i, pats in enumerate(patterns):
            if any(pat in text for pat in pats):
                matched[i].add(idx)

    matrix = [[len(matched[i] & matched[j]) for j in range(n)] for i in range(n)]

    return jsonify({"ok": True, "ids": ids, "labels": labels, "matrix": matrix})


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


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Analyse posts sent from the browser (bypasses server-side IP blocking)."""
    body = request.get_json(force=True, silent=True) or {}
    posts = body.get("posts", [])
    analysis_type = body.get("type", "symptoms")

    if not posts:
        return jsonify({"ok": False, "error": "no posts provided"}), 400

    if analysis_type == "keywords":
        top_n = int(body.get("top", 30))
        keywords = extract_keywords(posts, top_n=top_n)
        return jsonify({"ok": True, "keywords": keywords, "source": "live"})

    elif analysis_type == "correlation":
        top_n = int(body.get("top", 20))
        all_words = []
        for p in posts:
            text = p.get("title", "") + " " + p.get("selftext", "")
            tokens = re.findall(r"[a-z]{3,}", text.lower())
            all_words.extend(t for t in tokens if t not in STOPWORDS)

        top_keywords = [w for w, _ in Counter(all_words).most_common(top_n)]

        freq_matrix = []
        for p in posts:
            text = p.get("title", "") + " " + p.get("selftext", "")
            counts_p = Counter(re.findall(r"[a-z]{3,}", text.lower()))
            freq_matrix.append([counts_p.get(kw, 0) for kw in top_keywords])

        n = len(top_keywords)
        corr = [[0.0] * n for _ in range(n)]
        for i in range(n):
            corr[i][i] = 1.0
            col_i = [freq_matrix[r][i] for r in range(len(freq_matrix))]
            for j in range(i + 1, n):
                col_j = [freq_matrix[r][j] for r in range(len(freq_matrix))]
                rv = round(_pearson(col_i, col_j), 3)
                corr[i][j] = rv
                corr[j][i] = rv

        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                rv = corr[i][j]
                if rv != 0.0:
                    pairs.append({"word_a": top_keywords[i], "word_b": top_keywords[j], "r": rv})
        pairs.sort(key=lambda x: abs(x["r"]), reverse=True)

        return jsonify({
            "ok": True,
            "keywords": top_keywords,
            "matrix": corr,
            "pairs": pairs[:50],
            "source": "live",
        })

    else:  # symptoms
        counts = {symptom: 0 for symptom in SYMPTOMS}
        post_counts = {symptom: 0 for symptom in SYMPTOMS}

        for p in posts:
            text = (p.get("title", "") + " " + p.get("selftext", "")).lower()
            for symptom, patterns in SYMPTOMS.items():
                hits = sum(text.count(pat) for pat in patterns)
                counts[symptom] += hits
                if hits > 0:
                    post_counts[symptom] += 1

        results = [
            {"symptom": s, "mentions": counts[s], "posts": post_counts[s]}
            for s in SYMPTOMS if counts[s] > 0
        ]
        results.sort(key=lambda x: x["mentions"], reverse=True)

        return jsonify({
            "ok": True,
            "symptoms": results,
            "total_posts": len(posts),
            "source": "live",
        })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
