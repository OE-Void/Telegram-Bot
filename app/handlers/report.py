import logging
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.utils.helpers import delete_message, update_countdown_timer

# States
WAITING_FOR_REASON = 1

# Dictionary to track last report time per user
last_report_time = {}

logger = logging.getLogger(__name__)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the report conversation"""
    if not update.message:
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    current_time = datetime.now()
    
    # Check if user replied to a message
    if not update.message.reply_to_message:
        error_msg = await update.message.reply_text(
            "❌ Please reply to the message you want to report with /report"
        )
        # Schedule message deletion after 1 minute
        context.job_queue.run_once(
            delete_message,
            60.0,
            data={'chat_id': update.effective_chat.id, 'message_id': error_msg.message_id}
        )
        context.job_queue.run_once(
            delete_message,
            60.0,
            data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
        )
        return ConversationHandler.END
    
    # Check if reported user is an admin
    reported_user = update.message.reply_to_message.from_user
    if reported_user:
        try:
            chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            is_admin = any(admin.user.id == reported_user.id for admin in chat_admins)
            
            if is_admin:
                error_msg = await update.message.reply_text(
                    "😏 You think you are smart dumbass, reporting admins is not allowed"
                )
                context.job_queue.run_once(
                    delete_message,
                    60.0,
                    data={'chat_id': update.effective_chat.id, 'message_id': error_msg.message_id}
                )
                context.job_queue.run_once(
                    delete_message,
                    60.0,
                    data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
                )
                return ConversationHandler.END
        except Exception:
            pass
    
    # Check if user is in cooldown period
    if user_id in last_report_time:
        time_since_last_report = (current_time - last_report_time[user_id]).total_seconds()
        if time_since_last_report < 60:
            remaining_time = int(60 - time_since_last_report)
            cooldown_msg = await update.message.reply_text(
                f"⏳ Please wait {remaining_time} seconds before submitting another report."
            )
            
            # Start countdown timer
            context.job_queue.run_repeating(
                update_countdown_timer,
                interval=1.0,
                first=1.0,
                data={
                    'chat_id': update.effective_chat.id, 
                    'message_id': cooldown_msg.message_id,
                    'remaining': remaining_time,
                    'initial_time': remaining_time
                },
                name=f'countdown_{cooldown_msg.message_id}'
            )
            
            # Delete the command message
            context.job_queue.run_once(
                delete_message,
                60.0,
                data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
            )
            return ConversationHandler.END
    
    # Store the reported message info
    reported_msg = update.message.reply_to_message
    context.user_data['reported_message_id'] = reported_msg.message_id
    context.user_data['reported_user'] = reported_msg.from_user
    context.user_data['reported_message_text'] = reported_msg.text or reported_msg.caption or '[Media/Sticker/Other]'
    
    # Ask for reason by replying to this prompt
    prompt_msg = await update.message.reply_text(
        "📝 Reply to THIS message with the reason for your report.\n\n"
        "⏱️ You have 1 minute to respond or this request will be cancelled."
    )
    
    # Store the prompt message ID to delete later
    context.user_data['prompt_message_id'] = prompt_msg.message_id
    context.user_data['command_message_id'] = update.message.message_id
    
    # Schedule timeout (1 minute)
    context.job_queue.run_once(
        timeout_report,
        60.0,
        data={'chat_id': update.effective_chat.id, 'user_id': user_id, 'prompt_msg_id': prompt_msg.message_id, 'cmd_msg_id': update.message.message_id},
        name=f'report_timeout_{user_id}_{current_time.timestamp()}'
    )
    
    return WAITING_FOR_REASON

async def receive_report_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the report reason provided by user"""
    user_id = update.effective_user.id
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user replied to the bot's prompt message
    if not update.message.reply_to_message or update.message.reply_to_message.message_id != context.user_data.get('prompt_message_id'):
        # Ignore messages that are not replies to the prompt
        return WAITING_FOR_REASON
    
    reason = update.message.text
    
    # Cancel all timeout jobs for this user
    all_jobs = context.job_queue.jobs()
    for job in all_jobs:
        if job.name and job.name.startswith(f'report_timeout_{user_id}_'):
            job.schedule_removal()
    
    # Delete the prompt message
    try:
        if 'prompt_message_id' in context.user_data:
            await context.bot.delete_message(
                chat_id=chat.id,
                message_id=context.user_data['prompt_message_id']
            )
    except Exception:
        pass
    
    # Delete the command message
    try:
        if 'command_message_id' in context.user_data:
            await context.bot.delete_message(
                chat_id=chat.id,
                message_id=context.user_data['command_message_id']
            )
    except Exception:
        pass
    
    # Send confirmation to user
    confirmation_msg = await update.message.reply_text(
        "✅ Your report has been submitted to the admins.\n"
        "Thank you for helping keep the community safe."
    )
    
    # Schedule confirmation message deletion after 1 minute
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': chat.id, 'message_id': confirmation_msg.message_id}
    )
    
    # Get reported message details
    reported_user = context.user_data.get('reported_user')
    reported_msg_text = context.user_data.get('reported_message_text', 'N/A')
    
    # Get all admins in the chat
    try:
        chat_admins = await context.bot.get_chat_administrators(chat.id)
        logger.info(f"Found {len(chat_admins)} admins in chat {chat.id}")
        
        # Send report to each admin via DM
        report_text = (
            f"🚨 NEW REPORT\n\n"
            f"👤 Reporter: {user.full_name} (@{user.username or 'N/A'})\n"
            f"🆔 Reporter ID: {user_id}\n\n"
            f"🎯 Reported User: {reported_user.full_name if reported_user else 'Unknown'} (@{reported_user.username if reported_user and reported_user.username else 'N/A'})\n"
            f"📝 Reported Message: {reported_msg_text[:100]}{'...' if len(reported_msg_text) > 100 else ''}\n\n"
            f"💬 Chat: {chat.title or chat.first_name}\n"
            f"📋 Reason: {reason}\n"
            f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        admin_notified_count = 0
        for admin in chat_admins:
            # Skip bots and the reporter
            if admin.user.is_bot:
                continue
            if admin.user.id == user_id:
                continue
            
            try:
                await context.bot.send_message(
                    chat_id=admin.user.id,
                    text=report_text
                )
                admin_notified_count += 1
            except Exception as e:
                # Admin may have blocked the bot or never started it
                logger.warning(f"Failed to notify admin {admin.user.id}: {str(e)}")
                pass
        
        logger.info(f"Total admins notified: {admin_notified_count}")
    except Exception as e:
        logger.error(f"Error getting admins or sending reports: {str(e)}")
        pass
    
    # Update last report time
    last_report_time[user_id] = datetime.now()
    
    # Delete user's reason message after 1 minute
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': chat.id, 'message_id': update.message.message_id}
    )
    
    return ConversationHandler.END

async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the report conversation"""
    user_id = update.effective_user.id
    
    # Cancel all timeout jobs for this user
    all_jobs = context.job_queue.jobs()
    for job in all_jobs:
        if job.name and job.name.startswith(f'report_timeout_{user_id}_'):
            job.schedule_removal()
    
    cancel_msg = await update.message.reply_text("Report cancelled.")
    
    # Delete prompt message
    try:
        if 'prompt_message_id' in context.user_data:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['prompt_message_id']
            )
    except Exception:
        pass
    
    # Delete command message
    try:
        if 'command_message_id' in context.user_data:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['command_message_id']
            )
    except Exception:
        pass
    
    # Schedule cancel message deletion
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': cancel_msg.message_id}
    )
    
    # Delete cancel command message
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
    )
    
    return ConversationHandler.END

async def timeout_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timeout when user doesn't provide reason within 1 minute"""
    job_data = context.job.data
    chat_id = job_data['chat_id']
    prompt_msg_id = job_data.get('prompt_msg_id')
    cmd_msg_id = job_data.get('cmd_msg_id')
    
    try:
        timeout_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⏱️ Report request timed out. Please try again with /report."
        )
        
        # Schedule timeout message deletion
        context.job_queue.run_once(
            delete_message,
            60.0,
            data={'chat_id': chat_id, 'message_id': timeout_msg.message_id}
        )
        
        # Delete the prompt message
        if prompt_msg_id:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=prompt_msg_id
                )
            except Exception:
                pass
        
        # Delete the command message
        if cmd_msg_id:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=cmd_msg_id
                )
            except Exception:
                pass
    except Exception:
        pass
