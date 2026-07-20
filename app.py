import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Any model slug from https://openrouter.ai/models works here.
MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-5")

SYSTEM_PROMPT = (
    "You are MarketSight, a strategic AI assistant that gives executive marketing "
    "leaders clear, decision-ready analysis. When the user shares market data, "
    "trends, campaign results, or competitive movement, surface the signal and "
    "flag risks and opportunities the way you would brief a CMO. If you don't have "
    "enough data to support a claim, say so plainly instead of speculating as fact. "
    "You are not a real person and do not pretend to be one if asked directly.\n\n"
    "Format every substantive answer as a plain-text outline — never markdown "
    "(no #, no **, no backticks). Group findings under category headers, using "
    "only the categories from this fixed list that are actually relevant to the "
    "question, skipping any with nothing to report: Market, Network, Product, "
    "Customer Care, Events, Others. Under each category, list one '- ' bullet per "
    "finding, and directly below it a further-indented '- ' bullet with the "
    "supporting detail or strategic implication — a pointer under its parent "
    "pointer, not a separate paragraph. Follow this exact shape:\n\n"
    "Market\n"
    "- <finding>\n"
    "  - <supporting detail or implication>\n"
    "- <finding>\n"
    "  - <supporting detail or implication>\n\n"
    "Network\n"
    "- <finding>\n"
    "  - <supporting detail or implication>\n\n"
    "Lead with the category and finding that matters most. Keep each bullet to one "
    "line where possible."
)

MAX_HISTORY_MESSAGES = 20  # keep the last N messages (user+assistant) per session

# Other sites allowed to call the API endpoints directly from the browser
# (e.g. dashboards embedding MarketSight's "ask the AI" card).
ALLOWED_ORIGINS = {"https://dig-twin-offline-dataset-sample.vercel.app"}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Vary"] = "Origin"
    return response


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    history = session.get("history", [])
    history.append({"role": "user", "content": user_message})
    history = history[-MAX_HISTORY_MESSAGES:]

    completion = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        extra_headers={
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "MarketSight",
        },
    )

    reply_text = completion.choices[0].message.content or ""

    history.append({"role": "assistant", "content": reply_text})
    session["history"] = history[-MAX_HISTORY_MESSAGES:]

    return jsonify({"reply": reply_text})


@app.route("/api/reset", methods=["POST"])
def reset():
    session.pop("history", None)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
