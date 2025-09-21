import telebot
import os
import sys
from dotenv import load_dotenv
# Ensure project root is on sys.path so package imports work when running this file directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from chat.gemini import Chat, client as gem_client, model as gem_model

load_dotenv()

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_API"))
if not bot:
    raise Exception("TELEGRAM_BOT_API is not set in .env file")


# Instantiate the Gemini Chat wrapper once and reuse it
gem_chat = Chat(gem_client, gem_model)

# Track active users (by user_id)
active_users = set()

class BotHandlers:
    @bot.message_handler(commands=['help'])
    def help_cmd(message):
        bot.reply_to(message,
            "📖 Commands:\n"
            "/start - Activate AI chat (only for you)\n"
            "/close - Deactivate AI chat\n"
            "/help - Show this menu\n"
            "/models - Show the supported AI models"
        )

    @bot.message_handler(commands=['models'])
    def models_cmd(message):
        bot.reply_to(message,
            "📖 Common-Commands:\n"
            "/start - Activate AI chat (only for you)\n"
            "/close - Deactivate AI chat\n"
            "/help - Shows help menu\n\n"
            "🤖 Supported Gemini Models:\n"
            "- gemini-2.5-pro → Deep reasoning, multimodal (text, image, audio, video, PDF)\n"
            "- gemini-2.5-flash → Fast, cost-efficient, multimodal\n"
            "- gemini-2.5-flash-lite → Ultra low-latency, cost-optimized\n"
            "- gemini-live-2.5-flash-preview → Real-time voice/video interactions\n"
            "- gemini-2.5-flash-preview-native-audio-dialog → Natural conversational audio\n"
            "- gemini-2.5-flash-exp-native-audio-thinking-dialog → Audio + reasoning\n"
            "- gemini-2.5-flash-image-preview → Image generation/editing (preview)\n"
            "- gemini-2.5-flash-preview-tts → Text-to-speech (preview)\n"
            "- gemini-2.5-pro-preview-tts → High-quality text-to-speech (preview)\n"
            "- gemini-2.0-flash → Legacy fast model (still available in some regions)\n"
            "XenBOT selects best model for your task in the backend"
        )
            

    @bot.message_handler(commands=['start'])
    def start_cmd(message):
        user_id = message.from_user.id
        active_users.add(user_id)
        bot.reply_to(message, f"✅ AI chat activated for you, {message.from_user.first_name}!")

    @bot.message_handler(commands=['close'])
    def close_cmd(message):
        user_id = message.from_user.id
        if user_id in active_users:
            active_users.remove(user_id)
            bot.reply_to(message, "❌ AI chat deactivated for you.")
        else:
            bot.reply_to(message, "⚠️ You weren’t active.")
            
    @bot.message_handler(func=lambda m: True)
    def handle_message(message):
        user_id = message.from_user.id
        if user_id in active_users:
            # Call Gemini Chat and reply with the AI output
            try:
                ai_response = gem_chat.response(message.text)
            except Exception as e:
                bot.reply_to(message, f"⚠️ AI error: {e}")
                return

            bot.reply_to(message, f"{ai_response}")
        else:
            # Stay silent or just ignore
            pass

    