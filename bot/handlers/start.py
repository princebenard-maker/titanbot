from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.user_manager import get_or_create_user, is_admin
from bot.responses import WELCOME_MESSAGE, WELCOME_ADMIN_MESSAGE
from bot.handlers.admin import admin_sessions
from config.constants import ADMIN_TELEGRAM_ID
import logging

logger = logging.getLogger(__name__)

# Import admin sessions for auth visibility check
# Note: This is a circular import workaround - admin_sessions is set at module level

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
    is_admin_user = await is_admin(user_id)
    is_authenticated = user_id in admin_sessions
    
    # Base commands - visible to everyone
    msg = "Titan V1 Commands\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📌 General:\n"
    msg += "/start — Welcome message\n"
    msg += "/help — This message\n"
    msg += "/status — Your account status\n"
    msg += "/signal BTCUSDT — Generate signal\n"
    msg += "/regime BTCUSDT — Check market regime\n"
    msg += "/score BTCUSDT — View confidence score\n"
    msg += "/journal — View recent signals\n"
    msg += "/expectancy — System performance\n"
    
    # Admin commands - only visible after authentication
    if is_admin_user and is_authenticated:
        msg += "\n🔐 Admin (Authorized):\n"
        msg += "/dashboard — System overview\n"
        msg += "/users — All users\n"
        msg += "/pending — Pending approvals\n"
        msg += "/approve ID — Approve user\n"
        msg += "/reject ID — Reject user\n"
        msg += "/suspend ID — Suspend user\n"
        msg += "/resume ID — Resume user\n"
        msg += "/risk — View risk settings\n"
        msg += "/enable_trading — Enable trading\n"
        msg += "/disable_trading — Disable trading\n"
        msg += "/invite — Generate invite link\n"
        msg += "/healthcheck — System health\n"
        msg += "/logs — Audit trail\n"
    elif is_admin_user:
        msg += "\n🔐 Admin (Locked):\n"
        msg += "/authorize PIN — Login to unlock\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "⚠️ Admin commands locked.\nUse /authorize <PIN> to unlock."
    else:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "Contact admin for access."
    
    await update.message.reply_text(msg)

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
        "Ready for 21-day paper trading validation!"
    )

def register_start(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
