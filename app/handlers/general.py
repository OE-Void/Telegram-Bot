import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.utils.helpers import delete_message

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    start_text = (
        "👋 Welcome! Here are the commands you can use:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Help", callback_data='help'), InlineKeyboardButton("🔥 Roast", callback_data='roast')],
        [InlineKeyboardButton("🚨 Report", callback_data='report_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=start_text,
        reply_markup=reply_markup
    )
    
    # Delete command and response after 1 minute
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
    )
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': msg.message_id}
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    help_text = (
        "📚 *Available Commands*\n\n"
        "🌟 *General*\n"
        "`/start` - Start the bot\n"
        "`/help` - Show this message\n"
        "`/alive` - Check connection status\n\n"
        "🔥 *Fun*\n"
        "`/roast` - Get roasted (tag a user or yourself!)\n\n"
        "🛡️ *Moderation*\n"
        "`/report` - Report a message (Reply to msg)\n"
        "`/cancel` - Cancel active report\n\n"
        "👮‍♂️ *Admin Only*\n"
        "`/mute` - Mute a user (Reply to msg)\n"
        "`/unmute` - Unmute a user (Reply to msg)"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔥 Roast", callback_data='roast'), InlineKeyboardButton("🚨 Report Info", callback_data='report_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Delete command and response after 1 minute
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
    )
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': msg.message_id}
    )

async def alive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if bot is alive"""
    if not update.message:
        return
    
    user = update.effective_user
    mention = f"@{user.username}" if user.username else user.first_name
    
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Yup, I am alive {mention}!"
    )
    
    # Delete command and response after 1 minute
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
    )
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': msg.message_id}
    )

async def roast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    url = "https://evilinsult.com/generate_insult.php"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            roast_text = response.text
        else:
            roast_text = "Failed to fetch roast. here's the classic one: 'You're as useless as the 'ueue' in 'queue'."
    except requests.RequestException:
        roast_text = "Failed to fetch roast. here's the classic one: 'You're as useless as the 'ueue' in 'queue'."

    # Check if user replied to a message (roasting someone else)
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target_user = update.message.reply_to_message.from_user
        mention = f"@{target_user.username}" if target_user.username else target_user.first_name
        final_text = f"{mention} {roast_text}"
    else:
        # Roast the command user
        user = update.effective_user
        mention = f"@{user.username}" if user.username else user.first_name
        final_text = f"{mention} {roast_text}"
    
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=final_text)
    
    # Delete command and roast message after 1 minute
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
    )
    context.job_queue.run_once(
        delete_message,
        60.0,
        data={'chat_id': update.effective_chat.id, 'message_id': msg.message_id}
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        help_text = (
            "📚 *Available Commands*\n\n"
            "🌟 *General*\n"
            "`/start` - Start the bot\n"
            "`/help` - Show this message\n"
            "`/alive` - Check status\n\n"
            "🔥 *Fun*\n"
            "`/roast` - Get roasted (tag/self)\n\n"
            "🛡️ *Moderation*\n"
            "`/report` - Report a message\n"
            "`/cancel` - Cancel report\n\n"
            "👮‍♂️ *Admin Only*\n"
            "`/mute` - Mute user\n"
            "`/unmute` - Unmute user"
        )
        await query.edit_message_text(text=help_text, parse_mode='Markdown')
    elif query.data == 'roast':
        await query.edit_message_text(text="🔥 Use `/roast` command to get roasted!\n\nReply to someone's message with `/roast` to roast them, or just type `/roast` to roast yourself!", parse_mode='Markdown')
    elif query.data == 'report_info':
        await query.edit_message_text(text="🚨 *To report a message:*\n\n1. Reply to the offending message with `/report`\n2. The bot will ask for a reason\n3. Reply to the bot's message with your reason\n\n⚠️ You cannot report admins!", parse_mode='Markdown')
