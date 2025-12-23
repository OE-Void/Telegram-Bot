import logging
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes
from app.utils.helpers import delete_message, extract_status_change

logger = logging.getLogger(__name__)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome new members to the group"""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        
        # Get username or first name
        username = f"@{member.username}" if member.username else member.first_name
        
        welcome_text = (
            f"👋 Welcome {username}!\n\n"
            f"We're glad to have you here. Use ```/help``` to see available commands."
        )
        
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text
        )
        
        # Delete welcome message after 1 minute
        context.job_queue.run_once(
            delete_message,
            60.0,
            data={'chat_id': update.effective_chat.id, 'message_id': msg.message_id}
        )

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-accept group invitations"""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    
    was_member, is_member = result
    
    # Bot was added to a group
    if not was_member and is_member:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="👋 Hello! Thanks for adding me to the group. Use ```/help``` to see what I can do!"
        )

from telegram.error import BadRequest

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-approve join requests"""
    chat_join_request = update.chat_join_request
    
    if not chat_join_request:
        return
    
    try:
        await context.bot.approve_chat_join_request(
            chat_id=chat_join_request.chat.id,
            user_id=chat_join_request.from_user.id
        )
        logger.info(f"Auto-approved join request from user {chat_join_request.from_user.id} in chat {chat_join_request.chat.id}")
    except BadRequest as e:
        if "User_already_participant" in str(e):
            logger.info(f"User {chat_join_request.from_user.id} was already accepted or is a member.")
        else:
            logger.error(f"Failed to auto-approve join request: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to auto-approve join request: {str(e)}")

async def handle_pinned_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """React to pinned messages with fire emoji"""
    if not update.message:
        return
    
    # Check if this is a pinned message service update
    if not update.message.pinned_message:
        return
    
    # Get the pinned message
    pinned_msg = update.message.pinned_message
    
    try:
        # React to the pinned message with fire emoji
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=pinned_msg.message_id,
            reaction=[ReactionTypeEmoji(emoji="🔥")]
        )
        logger.info(f"Reacted to pinned message {pinned_msg.message_id} with fire emoji")
    except Exception as e:
        logger.error(f"Failed to react to pinned message: {str(e)}")
