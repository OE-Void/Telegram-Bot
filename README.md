# tg_bot

Run the Telegram bot and Gemini integration.

Required environment variables (set in your shell or a `.env` file):

- `GEMINI_API_KEY` - your Gemini API key
- `MODEL` - model id (e.g. `gemini-2.5-flash`)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token

Run:

```bash
python -m tg_bot.setup
```

This will validate environment variables and start the bot.
