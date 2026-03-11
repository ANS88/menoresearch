from flask import Flask, jsonify, render_template, request
from menopause_reddit import get_posts, get_comments

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


if __name__ == "__main__":
    app.run(debug=True, port=5001)
