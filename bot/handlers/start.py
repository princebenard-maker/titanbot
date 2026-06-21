from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.user_manager import get_or_create_user, is_admin
from bot.responses import WELCOME_MESSAGE, WELCOME_ADMIN_MESSAGE
from config.constants import ADMIN_TELEGRAM_ID
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    user = await get_or_create_user(user_id, username, first_name, last_name)
    
    if user_id == ADMIN_TELEGRAM_ID:
        await update.message.reply_text(WELCOME_ADMIN_MESSAGE)
    else:
        await update.message.reply_text(WELCOME_MESSAGE)
    logger.info(f"User {user_id} started the bot. State: {user['state']}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Titan V1 Commands\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "General:\n"
        "/start — Welcome message\n"
        "/help — This message\n"
        "/status — Your account status\n\n"
        "Admin (requires /authorize first):\n"
        "/authorize PIN — Admin login\n"
        "/dashboard — System overview\n"
        "/users — All users\n"
        "/invite — Generate invite link\n"
        "/healthcheck — System health\n"
        "/logs — Audit trail\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Titan V1 — Foundation Layer"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Your Titan Account\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Telegram ID: {user_id}\n"
        "Status: Active\n"
        "Wave: 1 — Foundation\n"
        "Trading: Not enabled yet\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Wave 2 coming soon."
    )

def register_start(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
