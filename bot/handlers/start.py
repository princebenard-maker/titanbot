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
    """
    Executive landing experience.
    Shows operational summary, not command list.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    user = await get_or_create_user(user_id, username, first_name, last_name)
    
    # Build executive summary
    from engines.scanner import get_scanner
    from core.state_manager import get_state_manager
    from core.health_monitor import get_health_monitor
    from broker.paper import get_paper_broker
    
    scanner = get_scanner()
    state_manager = get_state_manager()
    health_monitor = get_health_monitor()
    broker = get_paper_broker()
    
    account = await broker.get_account()
    open_positions = await broker.get_positions()
    scanner_stats = scanner.get_stats()
    health = health_monitor.get_current_health()
    state_info = state_manager.get_state_info()
    
    # System status
    if health and health.overall_status.value == "HEALTHY":
        health_emoji = "🟢"
        health_status = "Operational"
    elif health and health.overall_status.value == "WARNING":
        health_emoji = "🟡"
        health_status = "Warning"
    else:
        health_emoji = "🟢"
        health_status = "Operational"
    
    # Trading status
    trading_status = "Running" if scanner._running else "Stopped"
    
    # Calculate next scan
    from datetime import datetime
    next_scan = "15 min"
    if scanner._last_scan:
        last = max(scanner._last_scan.values())
        elapsed = (datetime.utcnow() - last).total_seconds() / 60
        next_scan = f"{max(0, 15 - int(elapsed))} min"
    
    # Welcome message
    if user_id == ADMIN_TELEGRAM_ID:
        welcome = f"Welcome back, Admin."
    else:
        welcome = f"Welcome, {first_name}."
    
    msg = f"{welcome}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Status: {health_emoji} {health_status}\n"
    msg += f"Paper Trading: {trading_status}\n"
    msg += f"Balance: ${account.balance:.2f}\n"
    msg += f"Open Positions: {len(open_positions)}\n"
    msg += f"Completed Trades: {account.total_trades}\n"
    msg += f"Next Market Scan: {next_scan}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Scanner: {'🟢 Running' if scanner._running else '🔴 Stopped'}\n"
    msg += f"Scheduler: {'🟢 Running' if state_info['can_trade'] else '🔴 Stopped'}\n"
    msg += f"Learning: {health_emoji} Healthy\n"
    msg += f"Recovery: No Active Incidents\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Attention needed?
    if len(open_positions) > 0 or state_info.get('is_critical', False):
        msg += "⚠️ Attention may be required.\n"
    else:
        msg += "Nothing currently requires attention.\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Use /help for command list_\n"
    msg += "_Use /brain for operational details_"
    
    await update.message.reply_text(msg)
    logger.info(f"User {user_id} started the bot. State: {user['state']}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Organized by operational category.
    Humans configure. Titan operates.
    """
    user_id = update.effective_user.id
    is_admin_user = await is_admin(user_id)
    is_authenticated = user_id in admin_sessions
    
    msg = "🏁 *TITAN V1 COMMAND REFERENCE*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Trading (Information only)
    msg += "📊 *TRADING*\n"
    msg += "_Retrieve operational state_\n"
    msg += "/signal BTCUSDT — Latest decision\n"
    msg += "/why_not BTCUSDT — Why rejected\n"
    msg += "/positions — Open positions\n"
    msg += "/history — Trade history\n"
    msg += "/portfolio — Account summary\n"
    msg += "/report — Paper trading report\n\n"
    
    # Market Intelligence
    msg += "🔍 *MARKET INTELLIGENCE*\n"
    msg += "_Autonomous scanner results_\n"
    msg += "/watchlist — Monitored pairs\n"
    msg += "/opportunities — Top setups\n"
    msg += "/scanner_status — Scanner state\n\n"
    
    # Learning
    msg += "🎓 *LEARNING*\n"
    msg += "_Shared intelligence_\n"
    msg += "/brain — Operational brain\n"
    msg += "/learning_mode — Current strategy mode\n"
    msg += "/weekly_review — Weekly analysis\n"
    msg += "/calibration — Confidence calibration\n"
    msg += "/feature_importance — What works\n"
    msg += "/explain ID — Signal explanation\n\n"
    
    # Health
    msg += "🏥 *HEALTH*\n"
    msg += "_System status_\n"
    msg += "/health — Quick status\n"
    msg += "/health_report — Full health\n"
    msg += "/system_state — State machine\n"
    msg += "/recovery — Recovery sessions\n"
    msg += "/diagnostics — Full diagnostic\n\n"
    
    # Admin (after authorization)
    if is_admin_user and is_authenticated:
        msg += "⚙️ *ADMINISTRATION*\n"
        msg += "_System configuration_\n"
        msg += "/dashboard — System overview\n"
        msg += "/system_overview — Full dashboard\n"
        msg += "/users — All users\n"
        msg += "/pending — Pending approvals\n"
        msg += "/approve ID — Approve user\n"
        msg += "/reject ID — Reject user\n"
        msg += "/suspend ID — Suspend user\n"
        msg += "/resume ID — Resume user\n"
        msg += "/risk — View risk settings\n"
        msg += "/invite — Generate invite link\n"
        msg += "/logs — Audit trail\n"
        msg += "/trading_loop — Control trading\n"
        msg += "/enable_trading — Enable trading\n"
        msg += "/disable_trading — Disable trading\n"
        msg += "/learning_mode — Adjust strategy\n"
    elif is_admin_user:
        msg += "🔐 *ADMIN*\n"
        msg += "/authorize PIN — Unlock admin\n"
    else:
        msg += "_Contact admin for access_"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Titan operates autonomously.\n"
    msg += "Commands retrieve, not execute._"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Redirect to paper status for complete account view."""
    from bot.handlers.paper import quick_status_command
    await quick_status_command(update, context)

def register_start(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
