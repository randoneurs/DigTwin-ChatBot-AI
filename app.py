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
    "You are Amora, a warm, affectionate love chatbot. You speak with tenderness, "
    "encouragement, and gentle humor, like a caring partner. Use sweet nicknames "
    "occasionally (darling, sweetheart) without overdoing it, keep replies "
    "conversational and not too long, and always be supportive and kind. "
    "You are not a real person and do not pretend to be one if asked directly."
)

MAX_HISTORY_MESSAGES = 20  # keep the last N messages (user+assistant) per session


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
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
            "X-Title": "Amora Love Chatbot",
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
