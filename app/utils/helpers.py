import logging
import time
import os
import requests
from datetime import datetime
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes

# Logger
logger = logging.getLogger(__name__)

async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a message after delay"""
    job_data = context.job.data
    chat_id = job_data['chat_id']
    message_id = job_data['message_id']
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        # Message may already be deleted
        pass

async def update_countdown_timer(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update countdown timer in real-time"""
    job_data = context.job.data
    chat_id = job_data['chat_id']
    message_id = job_data['message_id']
    remaining = job_data['remaining']
    
    remaining -= 1
    job_data['remaining'] = remaining
    
    if remaining <= 0:
        # Delete message when countdown reaches 0
        context.job.schedule_removal()
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass
    else:
        # Update message with new countdown
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"⏳ Please wait {remaining} seconds before submitting another report."
            )
        except Exception:
            pass

def extract_status_change(chat_member_update: ChatMemberUpdated) -> tuple[bool, bool] | None:
    """Extract status change from ChatMemberUpdated"""
    status_change = chat_member_update.difference().get("status")
    if status_change is None:
        return None
    
    old_status, new_status = status_change
    was_member = old_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
    is_member = new_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
    
    return was_member, is_member

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates"""
    logger.error(f'Update {update} caused error {context.error}')

def keep_alive():
    """Keep the service alive on Render by pinging itself"""
    # Render spins down free tier services after 15 mins of inactivity.
    # We ping it every 14 mins to keep it awake.
    url = os.getenv("RENDER_EXTERNAL_URL") 
    
    if not url:
        print("No RENDER_EXTERNAL_URL found. Keep-alive pinger disabled.")
        return

    # Ensure URL ends with / if needed, though simple GET works on root
    print(f"Starting keep-alive pinger for {url}")
    
    while True:
        time.sleep(14 * 60)  # Sleep 14 minutes
        try:
            requests.get(url, timeout=10)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Keep-alive ping sent to {url}")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")

async def check_is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat"""
    try:
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return any(admin.user.id == update.effective_user.id for admin in chat_admins)
    except Exception:
        return False
