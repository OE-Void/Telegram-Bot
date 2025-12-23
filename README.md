# TeleBot - XenArcAI Telegram Bot

A modular Telegram bot built with `python-telegram-bot`.

## Features
- **Moderation**: Mute/Unmute users, Reporting system.
- **Fun**: Roast commands.
- **Utility**: Welcome messages, Auto-accept join requests.

## Deployment

### Prerequisites
- Python 3.12+
- Telegram Bot Token

### Local Setup
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
4. Create `.env` file with your token:
   ```
   BOT_TOKEN=your_token_here
   ```
5. Run the bot:
   ```bash
   python -m app.main
   ```

### Render/Heroku Deployment
This repository includes a `Procfile` and `runtime.txt` for easy deployment.
1. Connect your repository to Render/Heroku.
2. Set the `BOT_TOKEN` environment variable in the dashboard.
3. Deploy!
