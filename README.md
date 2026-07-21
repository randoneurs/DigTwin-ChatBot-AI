# MarketSight — Your strategic assistance!

A web-based executive analytics assistant for marketing leaders, powered by [OpenRouter](https://openrouter.ai/) (OpenAI-compatible API giving access to many models, including Claude, GPT, Llama, etc.). MarketSight reads like an executive summary: it leads with the key finding, backs it with the supporting insight, and closes with the implication for marketing strategy.

The frontend is a single static `index.html` (no build step, no framework). A small Flask backend proxies chat requests to OpenRouter so your API key stays server-side and is only ever read from the environment — the browser never sees it.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your OpenRouter API key in `.env` (already created):
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
   Get/rotate keys at https://openrouter.ai/keys — treat this like a password; don't commit `.env` (it's already git-ignored).

3. (Optional) Choose a model by setting `OPENROUTER_MODEL` in `.env` — defaults to `anthropic/claude-sonnet-5`. Browse options at https://openrouter.ai/models.

4. Run the app:
   ```
   python app.py
   ```

5. Open http://localhost:5000 in your browser and start chatting.

## Notes

- Chat history is kept per browser session (server-side, in-memory via Flask sessions) and capped to the last 20 messages.
- Click "Reset" to start a new conversation.
- MarketSight's persona is defined in `SYSTEM_PROMPT` inside `app.py` — edit it to change tone/focus.
- Switch models anytime via the `OPENROUTER_MODEL` env var — no code changes needed.

## Embedding: syncing with a dashboard's Executive Summary / Synthesis cards

`POST /api/chat` accepts an optional `context` object alongside `message` so an
embedding dashboard (e.g. the "Ask the intelligence AI" widget sitting beside
its Executive Summary card) can keep MarketSight's answers grounded in what's
currently on screen:

```json
{
  "message": "What's driving the share movement?",
  "context": {
    "executiveSummary": "<current Executive Summary Card text>",
    "synthesis": "<current Synthesis Card text>",
    "filters": { "Area": "Sumatra", "Region": "Medan", "Period": "Q2 2026" }
  }
}
```

- `message` and `context` are both optional, but at least one must be present.
- If `context` is sent with an empty/omitted `message`, MarketSight treats it
  as a **resume** request: it returns a synthesized executive summary of the
  current cards instead of erroring, and that summary seeds the session so
  later questions in the same widget stay consistent with it.
- The calling origin must be in `ALLOWED_ORIGINS` in `app.py` (CORS is locked
  down to specific origins since the API key stays server-side).
