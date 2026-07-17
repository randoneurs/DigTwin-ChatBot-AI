# Amora — Love Chatbot

A simple static web-based chatbot with a warm, affectionate personality, powered by [OpenRouter](https://openrouter.ai/) (OpenAI-compatible API giving access to many models, including Claude, GPT, Llama, etc.).

This is a plain HTML/CSS/JS page — no backend or build step required. It calls the OpenRouter API directly from your browser.

## Setup

1. Open `index.html` in a browser (double-click it, or serve it with any static file server).

2. Click **API Key** in the header and paste your OpenRouter API key. Get one at https://openrouter.ai/keys — treat it like a password.

   Your key is stored only in your browser's `localStorage` and is sent only to OpenRouter; it is never committed to this repo or sent anywhere else.

3. Start chatting!

## Notes

- Chat history is kept in memory in the browser tab and capped to the last 20 messages. It resets on page reload.
- Click "Reset" to start a new conversation.
- The bot's personality is defined in `SYSTEM_PROMPT` and the model in `MODEL`, both near the top of the `<script>` block in `index.html` — edit them to change tone/style or switch models. Browse model options at https://openrouter.ai/models.
- Because the API key lives in the browser and is sent directly to OpenRouter, don't share a page/deployment with your key pre-filled — each visitor should use their own key.
