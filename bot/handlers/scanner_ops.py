"""
scanner_ops.py - TITAN V1 SCANNER OPERATIONS
Scanner commands for autonomous market scanning.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

logger = logging.getLogger(__name__)


async def scanner_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show market scanner status."""
    from engines.scanner import get_scanner
    
    scanner = get_scanner()
    stats = scanner.get_stats()
    
    status = "🟢 ACTIVE" if stats['running'] else "🔴 STOPPED"
    
    msg = f"📡 *MARKET SCANNER STATUS*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Status: {status}\n"
    msg += f"Watchlist: {stats['watchlist_size']} pairs\n"
    msg += f"Total Scans: {stats['total_scans']}\n"
    msg += f"Trade Signals: {stats['trade_signals']}\n"
    msg += f"Signal Rate: {stats['signal_rate']}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Scan Interval: 15 minutes*\n"
    msg += "*Mode: Autonomous*\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show scanner watchlist."""
    from engines.scanner import get_scanner
    
    scanner = get_scanner()
    watchlist = scanner.watchlist
    
    msg = "👁️ *SCANNER WATCHLIST*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, pair in enumerate(watchlist, 1):
        # Get cached result if available
        cached = scanner.get_cached_result(pair)
        if cached:
            status_icon = "🟢" if cached.status.value == "TRADE" else "⚪"
            score = f"[{cached.score}/40]"
        else:
            status_icon = "⚪"
            score = "[--]"
        
        msg += f"{status_icon} {pair} {score}\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"*Total: {len(watchlist)} pairs*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def opportunities_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top trading opportunities."""
    from engines.scanner import get_scanner, ScanStatus
    
    scanner = get_scanner()
    
    await update.message.reply_text("🔍 *Scanning markets...*", parse_mode='Markdown')
    
    opportunities = await scanner.get_top_opportunities(limit=5)
    
    if not opportunities:
        await update.message.reply_text(
            "❌ *No trade opportunities found*\n\n"
            "Market conditions may not meet criteria.",
            parse_mode='Markdown'
        )
        return
    
    msg = "🎯 *TOP OPPORTUNITIES*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, opp in enumerate(opportunities, 1):
        emoji = "🟢" if opp.score >= 35 else "🟡"
        msg += f"{emoji} #{i} *{opp.pair}*\n"
        msg += f"   Score: *{opp.score}/40*\n"
        msg += f"   Regime: {opp.regime}\n"
        msg += f"   Volume: {opp.volume_ratio:.2f}x\n"
        msg += f"   ATR: {opp.atr_pct:.2f}%\n"
        msg += f"   R:R: 1:{opp.risk_reward:.1f}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    msg += "*Use /signal PAIR to execute*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def why_not_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain why a pair was rejected."""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Usage: /why_not <PAIR>\n\n"
            "Example: /why_not BTCUSDT\n\n"
            "Shows detailed analysis of why pair wasn't signaled."
        )
        return
    
    pair = context.args[0].upper()
    
    await update.message.reply_text(f"🔍 *Analyzing {pair}...*", parse_mode='Markdown')
    
    from engines.scanner import get_scanner
    
    scanner = get_scanner()
    result = await scanner.get_why_not(pair)
    
    status_emoji = {
        "TRADE": "🟢",
        "REJECT": "🔴",
        "WAIT": "🟡",
        "LOW_VOLUME": "⚠️",
        "BAD_REGIME": "⚠️",
        "LOW_CONFIDENCE": "⚠️",
    }
    
    emoji = status_emoji.get(result.status.value, "⚪")
    
    msg = f"{emoji} *{pair} ANALYSIS*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Status: *{result.status.value}*\n"
    msg += f"Score: *{result.score}/40*\n"
    msg += f"Regime: {result.regime}\n"
    msg += f"Volume Ratio: {result.volume_ratio:.2f}x\n"
    msg += f"ATR: {result.atr_pct:.2f}%\n"
    
    if result.entry_price > 0:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*If Executed:*\n"
        msg += f"Entry: ${result.entry_price:.4f}\n"
        msg += f"Stop: ${result.stop_loss:.4f}\n"
        msg += f"Target: ${result.take_profit:.4f}\n"
        msg += f"R:R: 1:{result.risk_reward:.1f}\n"
    
    if result.rejection_reasons:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*⚠️ Rejection Reasons:*\n"
        for reason in result.rejection_reasons:
            msg += f"• {reason}\n"
    
    if result.confidence_breakdown:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*Score Breakdown:*\n"
        for factor, score in result.confidence_breakdown.items():
            bar = "█" * (score // 2) + "░" * (10 - score // 2)
            msg += f"{factor}: {bar} ({score})\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def brain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Titan's operational brain."""
    from engines.scanner import get_scanner
    from core.state_manager import get_state_manager
    from core.health_monitor import get_health_monitor
    from broker.scheduler import get_scheduler
    from broker.paper import get_paper_broker
    
    scanner = get_scanner()
    state_manager = get_state_manager()
    health_monitor = get_health_monitor()
    scheduler = get_scheduler()
    broker = get_paper_broker()
    
    state_info = state_manager.get_state_info()
    health = health_monitor.get_current_health()
    scanner_stats = scanner.get_stats()
    broker_account = await broker.get_account()
    open_positions = await broker.get_positions()
    
    # Overall status
    if health and health.overall_status.value == "HEALTHY":
        status = "🟢 HEALTHY"
    elif health and health.overall_status.value == "WARNING":
        status = "🟡 WARNING"
    else:
        status = "⚠️ CHECKING"
    
    msg = "🧠 *TITAN OPERATIONAL BRAIN*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"System: {status}\n"
    msg += f"Health Score: {health.health_score if health else 'N/A'}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # State
    msg += "*STATE MACHINE:*\n"
    msg += f"Current: {state_info['state']}\n"
    msg += f"Can Trade: {'Yes' if state_info['can_trade'] else 'No'}\n"
    msg += f"Critical: {'Yes' if state_info['is_critical'] else 'No'}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Scanner
    msg += "*MARKET SCANNER:*\n"
    msg += f"Mode: Autonomous\n"
    msg += f"Watchlist: {scanner_stats['watchlist_size']} pairs\n"
    msg += f"Scans: {scanner_stats['total_scans']}\n"
    msg += f"Signals Found: {scanner_stats['trade_signals']}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Trading
    msg += "*PAPER BROKER:*\n"
    msg += f"Balance: ${broker_account.balance:.2f}\n"
    msg += f"Open Positions: {len(open_positions)}\n"
    msg += f"Win Rate: {broker_account.win_rate:.1f}%\n"
    msg += f"Consecutive: {broker_account.consecutive_wins}W/{broker_account.consecutive_losses}L\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Scheduler
    msg += "*SCHEDULER:*\n"
    msg += f"Position Check: {scheduler.position_check_interval}s\n"
    msg += f"Health Check: {scheduler.health_check_interval}s\n"
    msg += f"Trading: {'Enabled' if scheduler._trading_enabled else 'Disabled'}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def system_overview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full system overview."""
    from engines.scanner import get_scanner
    from core.state_manager import get_state_manager
    from core.health_monitor import get_health_monitor
    from core.learning_engine import get_learning_engine
    from broker.paper import get_paper_broker
    from datetime import datetime
    
    scanner = get_scanner()
    state_manager = get_state_manager()
    health_monitor = get_health_monitor()
    learning = get_learning_engine()
    broker = get_paper_broker()
    
    account = await broker.get_account()
    scanner_stats = scanner.get_stats()
    health = health_monitor.get_current_health()
    state_info = state_manager.get_state_info()
    
    # Calculate uptime
    created = account.created_at
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    days_running = (datetime.utcnow() - created).days
    
    msg = "╔══════════════════════════════╗\n"
    msg += "║   🏁 TITAN SYSTEM OVERVIEW   ║\n"
    msg += "╠══════════════════════════════╣\n"
    
    # Account
    msg += f"║ 💰 ACCOUNT                    ║\n"
    msg += f"║ Balance: ${account.balance:.2f}             ║\n"
    msg += f"║ P&L: ${account.realized_pnl:+.2f}              ║\n"
    msg += f"║ Trades: {account.total_trades}               ║\n"
    msg += f"║ Win Rate: {account.win_rate:.1f}%            ║\n"
    msg += "╠══════════════════════════════╣\n"
    
    # Scanner
    msg += f"║ 📡 SCANNER                    ║\n"
    msg += f"║ Pairs: {scanner_stats['watchlist_size']}                   ║\n"
    msg += f"║ Signals: {scanner_stats['trade_signals']}               ║\n"
    msg += f"║ Rate: {scanner_stats['signal_rate']}            ║\n"
    msg += "╠══════════════════════════════╣\n"
    
    # Health
    msg += f"║ 🏥 HEALTH                     ║\n"
    msg += f"║ Score: {health.health_score if health else 'N/A'}%                 ║\n"
    msg += f"║ Status: {health.overall_status.value if health else 'N/A':8s}         ║\n"
    msg += "╠══════════════════════════════╣\n"
    
    # Learning
    mode_config = learning.get_mode_config()
    msg += f"║ 🎓 LEARNING                   ║\n"
    msg += f"║ Mode: {mode_config['mode']:11s}         ║\n"
    msg += f"║ Min Conf: {mode_config['min_confidence']}                 ║\n"
    msg += f"║ Max Risk: {mode_config['max_risk_percent']}%               ║\n"
    msg += "╠══════════════════════════════╣\n"
    
    # Progress
    msg += f"║ 📊 PROGRESS                   ║\n"
    msg += f"║ Day: {days_running} of 21              ║\n"
    msg += f"║ Trades: {account.total_trades} of 100           ║\n"
    msg += "╚══════════════════════════════╝"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def trading_loop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Control trading loop."""
    from broker.scheduler import get_scheduler
    from engines.scanner import get_scanner
    
    if not context.args:
        scheduler = get_scheduler()
        scanner = get_scanner()
        
        trading_status = "🟢 ENABLED" if scheduler._trading_enabled else "🔴 DISABLED"
        scanner_status = "🟢 ACTIVE" if scanner._running else "🔴 STOPPED"
        
        msg = "⚙️ *TRADING LOOP STATUS*\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"Trading: {trading_status}\n"
        msg += f"Scanner: {scanner_status}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*Control Commands:*\n"
        msg += "/loop start - Enable trading\n"
        msg += "/loop stop - Disable trading\n"
        msg += "/loop pause - Pause scanner\n"
        msg += "/loop resume - Resume scanner"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    action = context.args[0].lower()
    scheduler = get_scheduler()
    scanner = get_scanner()
    
    if action == "start":
        scheduler.enable_trading()
        await update.message.reply_text("✅ *Trading enabled*")
    elif action == "stop":
        scheduler.disable_trading()
        await update.message.reply_text("⛔ *Trading disabled*")
    elif action == "pause":
        await scanner.stop()
        await update.message.reply_text("⏸️ *Scanner paused*")
    elif action == "resume":
        await scanner.start()
        await update.message.reply_text("▶️ *Scanner resumed*")
    else:
        await update.message.reply_text(f"❌ Unknown action: {action}")


async def addpair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add pair to watchlist (admin)."""
    from core.user_manager import is_admin
    
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /addpair <PAIR>\n\nExample: /addpair MATICUSDT")
        return
    
    pair = context.args[0].upper()
    
    from engines.scanner import get_scanner
    scanner = get_scanner()
    await scanner.add_to_watchlist(pair)
    
    await update.message.reply_text(f"✅ *{pair} added to watchlist*")


async def removepair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove pair from watchlist (admin)."""
    from core.user_manager import is_admin
    
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /removepair <PAIR>")
        return
    
    pair = context.args[0].upper()
    
    from engines.scanner import get_scanner
    scanner = get_scanner()
    await scanner.remove_from_watchlist(pair)
    
    await update.message.reply_text(f"✅ *{pair} removed from watchlist*")


def register_scanner_ops(app):
    """Register scanner operation commands."""
    app.add_handler(CommandHandler("scanner_status", scanner_status_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("opportunities", opportunities_command))
    app.add_handler(CommandHandler("why_not", why_not_command))
    app.add_handler(CommandHandler("brain", brain_command))
    app.add_handler(CommandHandler("system_overview", system_overview_command))
    app.add_handler(CommandHandler("trading_loop", trading_loop_command))
    app.add_handler(CommandHandler("addpair", addpair_command))
    app.add_handler(CommandHandler("removepair", removepair_command))
    
    logger.info("Scanner operations registered")
