# Amora — Love Chatbot

A simple web-based chatbot with a warm, affectionate personality, powered by [OpenRouter](https://openrouter.ai/) (OpenAI-compatible API giving access to many models, including Claude, GPT, Llama, etc.).

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
- The bot's personality is defined in `SYSTEM_PROMPT` inside `app.py` — edit it to change tone/style.
- Switch models anytime via the `OPENROUTER_MODEL` env var — no code changes needed.
