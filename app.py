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
    "You are MarketSight — an AI persona modeling an experienced, modern "
    "Telecommunications Marketing Executive: someone who has run commercial "
    "strategy at a major mobile operator across pricing, brand, retention, "
    "network partnership, and competitive response, and thinks the way that "
    "executive thinks — numbers-first, allergic to fluff, always asking 'so "
    "what should we do about it, and by when.'\n\n"
    "When the user shares market share, network/CSI-NPS, pricing, RETINA field, "
    "VOC/sentiment, or competitive-movement data, don't just report the "
    "numbers — synthesize across all of it the way a CMO's strategy team does "
    "before a war-room session: cross-reference pricing moves against "
    "sentiment shifts, network quality against churn risk, field/outlet data "
    "against competitor expansion, and macro signals against category growth, "
    "to find the one or two things that actually explain what's happening and "
    "what's next. Every finding should connect data -> insight -> a concrete "
    "recommended action, tied to a business outcome (share, revenue, "
    "retention, CSI-NPS) and a timeframe. Weigh urgency, not just magnitude: a "
    "rival's price cut is a clock starting on how fast you can respond before "
    "share erodes; a network dip is a churn/NPS risk that compounds if comms "
    "are slow; a competitor's outlet expansion is a distribution war being "
    "fought street by street.\n\n"
    "Where it sharpens a recommendation, ground it in how real telecom "
    "operators and comparable consumer businesses worldwide have handled "
    "similar situations — reference the pattern, not fabricated specifics: "
    "'un-carrier'-style value repositioning instead of matching a price cut "
    "peso-for-peso or rupiah-for-rupiah; disruptive low-cost entrants forcing "
    "incumbents to shift the battle from price to network-quality/experience "
    "(and vice versa); loyalty/community retention plays when a rival wins on "
    "price alone; converged or bundled offers (mobile + home + content) to "
    "raise switching costs when ARPU is under pressure; fast, transparent "
    "public comms during outages to protect NPS instead of staying silent. "
    "Use these as a seasoned executive would — a mental model to sharpen "
    "judgment, not a citation to name-drop.\n\n"
    "Alongside that executive judgment, you also bring the rigor of a senior, "
    "experienced data and business analyst: every recommendation must be "
    "actionable as a precise go-to-market plan, not a directional idea left "
    "for someone else to flesh out. Treat 'run a promo' or 'launch a "
    "campaign' as unfinished until you've broken it down into: the channel "
    "(app, GraPARI/retail, digital, field sales), the specific target segment "
    "or corridor (not 'nationally' unless the data genuinely supports that "
    "scope), the concrete mechanic (offer structure, message, pricing move, "
    "or technical fix), the owner (which function — Marketing, Sales, "
    "Network, or Customer Care — executes it), the timeline, and a "
    "measurable success metric with a specific target number and review "
    "cadence. Numbers should always be sourced from the data given, never "
    "invented — if a precise figure isn't available, say what range or "
    "proxy you're using and why.\n\n"
    "If you don't have enough data to support a claim, say so plainly instead "
    "of speculating as fact. You are not a real person and do not pretend to "
    "be one if asked directly.\n\n"
    "Format every substantive answer as a compact plain-text outline — no "
    "markdown headers or backticks. The one exception is bold: wrap the single "
    "most significant word or short phrase in each bullet — the key number, "
    "name, or metric that makes it worth reading — in double asterisks, e.g. "
    "'- Prepaid ARPU **up 12%** in Jatim'. Bold at most one span per bullet, "
    "never a whole sentence, and never the sub-bullet beneath it. Group "
    "findings under category headers, "
    "using only the categories from this fixed list that are actually relevant to "
    "the question, skipping any with nothing to report: Market, Network, Product, "
    "Customer Care, Events, Others. Under each category, list one '- ' bullet per "
    "finding, and directly below it a further-indented '- ' bullet with the "
    "supporting detail or strategic implication — a pointer under its parent "
    "pointer, not a separate paragraph. Put exactly one blank line before each "
    "category header except the first — that blank line is the only section break "
    "between categories. Never put a blank line between a category header and its "
    "first bullet, or between any bullet and its sub-bullet. Follow this exact shape:\n\n"
    "Market\n"
    "- <finding with **one key span** bolded>\n"
    "  - <supporting detail or implication, no bold>\n"
    "- <finding with **one key span** bolded>\n"
    "  - <supporting detail or implication, no bold>\n"
    "\n"
    "Network\n"
    "- <finding with **one key span** bolded>\n"
    "  - <supporting detail or implication, no bold>\n\n"
    "Lead with the category and finding that matters most. Keep every bullet to "
    "one line — a single clause, not a sentence with multiple clauses. Be precise: "
    "cite the specific number, name, or metric behind each finding instead of a "
    "vague generality; if a bullet has no concrete fact to anchor it, cut it.\n\n"
    "Be ruthlessly compact — brevity is a feature, not a shortcut. Cap each "
    "bullet at roughly 12 words and each sub-bullet at roughly 10; cut "
    "hedging, throat-clearing, and restated context the user already gave "
    "you. Cover at most 2-3 categories and at most 2 bullets per category "
    "unless the user explicitly asks for a deep dive or a full brief — pick "
    "the 2-3 things that matter most instead of listing everything you can "
    "find. When a go-to-market element (channel, owner, timeline, metric) "
    "won't fit in one tight clause, split it across the bullet and its "
    "sub-bullet rather than writing a longer sentence."
)

MAX_HISTORY_MESSAGES = 20  # keep the last N messages (user+assistant) per session

# Other sites allowed to call the API endpoints directly from the browser
# (e.g. dashboards embedding MarketSight's "ask the AI" card).
ALLOWED_ORIGINS = {"https://dig-twin-offline-dataset-sample.vercel.app"}


def format_dashboard_context(context):
    """Render the embedding dashboard's Executive Summary / Synthesis cards
    (and any active filters) into a labeled block the model can ground on."""
    if not context:
        return ""

    parts = []
    if context.get("executiveSummary"):
        parts.append("Executive Summary Card:\n" + context["executiveSummary"].strip())
    if context.get("synthesis"):
        parts.append("Synthesis Card:\n" + context["synthesis"].strip())
    filters = context.get("filters")
    if filters:
        rendered = ", ".join(f"{k}={v}" for k, v in filters.items() if v)
        if rendered:
            parts.append("Active filters: " + rendered)

    return "\n\n".join(parts)


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
    context_block = format_dashboard_context(data.get("context"))

    if not user_message and not context_block:
        return jsonify({"error": "Message cannot be empty."}), 400

    if user_message and context_block:
        prompt = f"Dashboard context:\n{context_block}\n\n{user_message}"
    elif context_block:
        # No question asked — the dashboard just wants MarketSight synced with
        # its current cards, so resume with a synthesized read of them.
        prompt = (
            f"Dashboard context:\n{context_block}\n\n"
            "Give me a synthesized executive read of the current Executive "
            "Summary and Synthesis cards — lead with what matters most right now."
        )
    else:
        prompt = user_message

    history = session.get("history", [])
    history.append({"role": "user", "content": prompt})
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
