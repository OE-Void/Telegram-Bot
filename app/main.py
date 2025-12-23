import logging
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ChatMemberHandler, ChatJoinRequestHandler, 
    ConversationHandler, filters
)
from app.config import TOKEN
from app.utils.helpers import keep_alive, error_handler
from app.web_server import start_server_thread

from app.handlers.general import start_command, help_command, roast_command, alive_command, button_callback
from app.handlers.admin import mute_command, unmute_command
from app.handlers.report import report_command, receive_report_reason, cancel_report, WAITING_FOR_REASON
from app.handlers.events import welcome_new_member, handle_pinned_message, handle_chat_member_update, handle_join_request

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Silence httpx logs (too noisy)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    print('Starting bot...')

    # Start dummy web server for Render port binding
    start_server_thread()
    
    # Start keep-alive thread
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # Build application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers (group 0 - highest priority)
    app.add_handler(CommandHandler('start', start_command), group=0)
    app.add_handler(CommandHandler('help', help_command), group=0)
    app.add_handler(CommandHandler('roast', roast_command), group=0)
    app.add_handler(CommandHandler('mute', mute_command), group=0)
    app.add_handler(CommandHandler('unmute', unmute_command), group=0)
    app.add_handler(CommandHandler('alive', alive_command), group=0)
    
    # Add conversation handler for /report
    report_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_command)],
        states={
            WAITING_FOR_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_report_reason)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_report)],
        conversation_timeout=60
    )
    
    app.add_handler(report_conv_handler, group=0)
    
    # Add callback query handler for buttons
    app.add_handler(CallbackQueryHandler(button_callback), group=0)
    
    # Add status update handlers (group 1)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member), group=1)
    app.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, handle_pinned_message), group=1)
    
    # Add special handlers (group 1)
    app.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER), group=1)
    app.add_handler(ChatJoinRequestHandler(handle_join_request), group=1)
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Start polling
    print('Bot is running...')
    app.run_polling(poll_interval=3, allowed_updates=Update.ALL_TYPES)
