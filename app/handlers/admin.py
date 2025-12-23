from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from app.utils.helpers import delete_message, check_is_admin

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mute a user (admin only)"""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    # Check if user is admin
    if not await check_is_admin(update, context):
        error_msg = await update.message.reply_text("❌ Nice try Dumbass! Only admins can use this command.")
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
        return
    
    # Check if user replied to a message
    if not update.message.reply_to_message:
        error_msg = await update.message.reply_text("❌ Please reply to a user's message to mute them.")
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
        return
    
    target_user = update.message.reply_to_message.from_user
    
    # Check if target is admin (fetch admins again to check target)
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        is_target_admin = any(admin.user.id == target_user.id for admin in chat_admins)
        if is_target_admin:
            error_msg = await update.message.reply_text("❌ Cannot mute administrators.")
            context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
            context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
            return
    except Exception:
        pass
    
    # Mute user
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=permissions
        )
        
        success_msg = await update.message.reply_text(
            f"🔇 {target_user.first_name} has been muted."
        )
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': success_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
    except Exception as e:
        error_msg = await update.message.reply_text(f"❌ Failed to mute user: {str(e)}")
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unmute a user (admin only)"""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    
    # Check if user is admin
    if not await check_is_admin(update, context):
        error_msg = await update.message.reply_text("❌ Only admins can use this command.")
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
        return
    
    # Check if user replied to a message
    if not update.message.reply_to_message:
        error_msg = await update.message.reply_text("❌ Please reply to a user's message to unmute them.")
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
        return
    
    target_user = update.message.reply_to_message.from_user
    
    # Unmute user by restoring permissions
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=permissions
        )
        
        success_msg = await update.message.reply_text(
            f"🔊 {target_user.first_name} has been unmuted."
        )
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': success_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
    except Exception as e:
        error_msg = await update.message.reply_text(f"❌ Failed to unmute user: {str(e)}")
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': error_msg.message_id})
        context.job_queue.run_once(delete_message, 60.0, data={'chat_id': chat_id, 'message_id': update.message.message_id})
