import hashlib, hmac, os, logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.user_manager import is_admin, get_user, get_all_users, update_user_state
from core.audit import log_event, get_latest_audit_logs
from bot.responses import (
    ADMIN_AUTHORIZED_MESSAGE,
    ADMIN_UNAUTHORIZED_MESSAGE,
    ADMIN_ALREADY_AUTHORIZED_MESSAGE,
    NOT_AUTHORIZED_MESSAGE,
    USER_PENDING_APPROVAL_MESSAGE,
    USER_REJECTED_MESSAGE,
    USER_PAUSED_MESSAGE,
    USER_SUSPENDED_MESSAGE,
    DASHBOARD_MESSAGE,
    USERS_LIST_MESSAGE,
    NO_USERS_MESSAGE,
    INVITE_MESSAGE,
    HEALTHCHECK_MESSAGE,
    NO_AUDIT_LOGS_MESSAGE,
    AUDIT_LOGS_MESSAGE,
    INVALID_COMMAND_MESSAGE,
    PENDING_USERS_MESSAGE,
    NO_PENDING_USERS_MESSAGE,
    USER_APPROVED_MESSAGE,
    USER_REJECTED_MESSAGE,
    USER_SUSPENDED_MESSAGE,
    USER_RESUMED_MESSAGE,
    USER_NOT_FOUND_MESSAGE,
    TRADING_ENABLED_MESSAGE,
    TRADING_DISABLED_MESSAGE,
    RISK_SETTINGS_MESSAGE,
    INVALID_USER_ID_MESSAGE
)
from config.settings import ADMIN_PIN_HASH, ADMIN_TELEGRAM_ID
from config.constants import (
    USER_STATE_ACTIVE,
    USER_STATE_PENDING_APPROVAL,
    USER_STATE_SUSPENDED,
    USER_STATE_REJECTED,
    USER_STATE_TRADING_DISABLED
)

logger = logging.getLogger(__name__)

# In-memory trading state (persists until restart)
_trading_enabled = True

# Default risk settings
_risk_settings = {
    'max_position': 10,
    'stop_loss': 2.0,
    'take_profit': 6.0,
    'daily_limit': 3
}

# In-memory storage for admin sessions (for simplicity, not persistent)
admin_sessions = set()

async def check_admin_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return False
    if user_id not in admin_sessions:
        await update.message.reply_text("Admin not authorized. Please use /authorize <PIN>.")
        return False
    return True

async def authorize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return

    if user_id in admin_sessions:
        await update.message.reply_text(ADMIN_ALREADY_AUTHORIZED_MESSAGE)
        return

    try:
        pin = context.args[0]
    except IndexError:
        await update.message.reply_text("Usage: /authorize <PIN>")
        return

    # Admin PIN verification
    valid = hmac.compare_digest(
        hashlib.sha256(pin.encode()).hexdigest(),
        ADMIN_PIN_HASH
    )

    if valid:
        admin_sessions.add(user_id)
        await update.message.reply_text(ADMIN_AUTHORIZED_MESSAGE)
        await log_event("INFO", f"Admin {user_id} authorized.")
    else:
        await update.message.reply_text(ADMIN_UNAUTHORIZED_MESSAGE)
        await log_event("WARNING", f"Admin {user_id} failed authorization attempt.")
    
    # Delete the message containing the PIN for security
    if update.message.chat.type == 'private': # Only delete in private chats
        await update.message.delete()

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin_auth(update, context):
        return

    users = await get_all_users()
    active_users = sum(1 for u in users if u['state'] == USER_STATE_ACTIVE)
    pending_users = sum(1 for u in users if u['state'] == USER_STATE_PENDING_APPROVAL)
    total_users = len(users)

    await update.message.reply_text(
        DASHBOARD_MESSAGE.format(
            active_users=active_users,
            pending_users=pending_users,
            total_users=total_users
        ),
        parse_mode='Markdown'
    )
    await log_event("INFO", f"Admin {update.effective_user.id} viewed dashboard.")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin_auth(update, context):
        return

    users = await get_all_users()
    if not users:
        await update.message.reply_text(NO_USERS_MESSAGE)
        return

    user_list_str = ""
    for user in users:
        user_list_str += f"- ID: {user['telegram_id']}, Username: @{user['username'] or 'N/A'}, State: {user['state']}\n"
    
    await update.message.reply_text(
        USERS_LIST_MESSAGE.format(user_list=user_list_str),
        parse_mode='Markdown'
    )
    await log_event("INFO", f"Admin {update.effective_user.id} viewed user list.")

async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin_auth(update, context):
        return
    
    # For V1, invite link is just a placeholder. In a real scenario, this would generate a unique token.
    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start=invite"
    await update.message.reply_text(INVITE_MESSAGE.format(invite_link=invite_link))
    await log_event("INFO", f"Admin {update.effective_user.id} generated invite link.")

async def healthcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin_auth(update, context):
        return
    
    # Check DB status by trying to read one audit log
    last_log = await get_latest_audit_logs(limit=1)
    last_log_str = last_log[0]['timestamp'] if last_log else "N/A"

    await update.message.reply_text(
        HEALTHCHECK_MESSAGE.format(last_audit_log=last_log_str),
        parse_mode='Markdown'
    )
    await log_event("INFO", f"Admin {update.effective_user.id} performed healthcheck.")

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin_auth(update, context):
        return
    
    logs = await get_latest_audit_logs(limit=20)
    if not logs:
        await update.message.reply_text(NO_AUDIT_LOGS_MESSAGE)
        return

    logs_str = ""
    for log in logs:
        logs_str += f"`{log['timestamp']}` [{log['level']}] {log['message']} (Context: {log['context'] or 'N/A'})\n"
    
    await update.message.reply_text(
        AUDIT_LOGS_MESSAGE.format(logs=logs_str),
        parse_mode='Markdown'
    )
    await log_event("INFO", f"Admin {update.effective_user.id} viewed audit logs.")

# ==================== WAVE 2B ADMIN COMMANDS ====================

async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all pending users awaiting approval."""
    if not await check_admin_auth(update, context):
        return
    
    users = await get_all_users()
    pending = [u for u in users if u['state'] == USER_STATE_PENDING_APPROVAL]
    
    if not pending:
        await update.message.reply_text(NO_PENDING_USERS_MESSAGE)
        return
    
    user_list = ""
    for user in pending:
        user_list += f"• ID: `{user['telegram_id']}` | @{user['username'] or 'N/A'} | {user['first_name'] or 'N/A'}\n"
    
    await update.message.reply_text(
        PENDING_USERS_MESSAGE.format(user_list=user_list),
        parse_mode='Markdown'
    )
    await log_event("INFO", f"Admin {update.effective_user.id} viewed pending users.")


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve a user by telegram_id."""
    if not await check_admin_auth(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text(USER_NOT_FOUND_MESSAGE.format(user_id=user_id))
        return
    
    await update_user_state(user_id, USER_STATE_ACTIVE)
    await update.message.reply_text(USER_APPROVED_MESSAGE.format(user_id=user_id))
    await log_event("INFO", f"Admin {update.effective_user.id} approved user {user_id}.")


async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reject a user by telegram_id."""
    if not await check_admin_auth(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text(USER_NOT_FOUND_MESSAGE.format(user_id=user_id))
        return
    
    await update_user_state(user_id, USER_STATE_REJECTED)
    await update.message.reply_text(USER_REJECTED_MESSAGE.format(user_id=user_id))
    await log_event("INFO", f"Admin {update.effective_user.id} rejected user {user_id}.")


async def suspend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Suspend a user by telegram_id."""
    if not await check_admin_auth(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text(USER_NOT_FOUND_MESSAGE.format(user_id=user_id))
        return
    
    await update_user_state(user_id, USER_STATE_SUSPENDED)
    await update.message.reply_text(USER_SUSPENDED_MESSAGE.format(user_id=user_id))
    await log_event("INFO", f"Admin {update.effective_user.id} suspended user {user_id}.")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume a suspended user by telegram_id."""
    if not await check_admin_auth(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(INVALID_USER_ID_MESSAGE)
        return
    
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text(USER_NOT_FOUND_MESSAGE.format(user_id=user_id))
        return
    
    await update_user_state(user_id, USER_STATE_ACTIVE)
    await update.message.reply_text(USER_RESUMED_MESSAGE.format(user_id=user_id))
    await log_event("INFO", f"Admin {update.effective_user.id} resumed user {user_id}.")


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current risk settings."""
    if not await check_admin_auth(update, context):
        return
    
    await update.message.reply_text(
        RISK_SETTINGS_MESSAGE.format(
            max_position=_risk_settings['max_position'],
            stop_loss=_risk_settings['stop_loss'],
            take_profit=_risk_settings['take_profit'],
            daily_limit=_risk_settings['daily_limit']
        ),
        parse_mode='Markdown'
    )
    await log_event("INFO", f"Admin {update.effective_user.id} viewed risk settings.")


async def enable_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable trading system-wide."""
    global _trading_enabled
    if not await check_admin_auth(update, context):
        return
    
    _trading_enabled = True
    await update.message.reply_text(TRADING_ENABLED_MESSAGE)
    await log_event("INFO", f"Admin {update.effective_user.id} enabled trading.")


async def disable_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable trading system-wide."""
    global _trading_enabled
    if not await check_admin_auth(update, context):
        return
    
    _trading_enabled = False
    await update.message.reply_text(TRADING_DISABLED_MESSAGE)
    await log_event("INFO", f"Admin {update.effective_user.id} disabled trading.")


def is_trading_enabled() -> bool:
    """Check if trading is enabled."""
    return _trading_enabled


def register_admin(application):
    application.add_handler(CommandHandler("authorize", authorize_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("healthcheck", healthcheck_command))
    application.add_handler(CommandHandler("logs", logs_command))
    # Wave 2B Admin Commands
    application.add_handler(CommandHandler("pending", pending_command))
    application.add_handler(CommandHandler("approve", approve_command))
    application.add_handler(CommandHandler("reject", reject_command))
    application.add_handler(CommandHandler("suspend", suspend_command))
    application.add_handler(CommandHandler("resume", resume_command))
    application.add_handler(CommandHandler("risk", risk_command))
    application.add_handler(CommandHandler("enable_trading", enable_trading_command))
    application.add_handler(CommandHandler("disable_trading", disable_trading_command))
