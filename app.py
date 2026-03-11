from flask import Flask, jsonify, render_template, request
from menopause_reddit import get_posts, get_comments

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/posts")
def api_posts():
    category = request.args.get("category", "hot")
    limit = int(request.args.get("limit", 10))
    try:
        posts = get_posts(category=category, limit=limit)
        return jsonify({"ok": True, "posts": posts})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/comments")
def api_comments():
    permalink = request.args.get("permalink", "")
    if not permalink:
        return jsonify({"ok": False, "error": "permalink required"}), 400
    try:
        comments = get_comments(permalink, limit=10)
        return jsonify({"ok": True, "comments": comments})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
