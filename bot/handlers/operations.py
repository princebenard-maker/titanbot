"""
operations.py - WAVE 2C/2D
Titan Operations and Learning Commands
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.state_manager import get_state_manager, SystemState
from core.health_monitor import get_health_monitor, HealthStatus
from core.recovery_engine import get_recovery_engine
from core.learning_engine import get_learning_engine, FailureType

logger = logging.getLogger(__name__)

# ==================== OPERATIONAL COMMANDS ====================

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quick health check - overall status only."""
    health_monitor = get_health_monitor()
    health = health_monitor.get_current_health()
    
    if not health:
        await update.message.reply_text("⚠️ Health check not yet run. Use /health_report for full details.")
        return
    
    status_emoji = {
        HealthStatus.HEALTHY: "✅",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.CRITICAL: "🚨",
        HealthStatus.UNKNOWN: "❓"
    }
    
    emoji = status_emoji.get(health.overall_status, "❓")
    
    await update.message.reply_text(
        f"{emoji} TITAN HEALTH: {health.overall_status.value}\n"
        f"Score: {health.health_score}%\n"
        f"Last check: {health.last_full_check.strftime('%H:%M:%S')}"
    )


async def health_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Full health report with all subsystems."""
    health_monitor = get_health_monitor()
    health = await health_monitor.run_full_check()
    
    if not health:
        await update.message.reply_text("⚠️ Health check failed.")
        return
    
    status_emoji = {
        HealthStatus.HEALTHY: "✅",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.CRITICAL: "🚨",
        HealthStatus.UNKNOWN: "❓"
    }
    
    msg = f"🏥 TITAN HEALTH REPORT\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Score: {health.health_score}% | Status: {health.overall_status.value}\n"
    msg += f"Check duration: {health.check_duration_ms:.1f}ms\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    
    for name, subsystem in health.subsystems.items():
        emoji = status_emoji.get(subsystem.status, "❓")
        msg += f"{emoji} {name.upper()}\n"
        msg += f"   {subsystem.message}\n"
        if subsystem.response_time_ms > 0:
            msg += f"   Response: {subsystem.response_time_ms:.1f}ms\n"
    
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Checked: {health.last_full_check.strftime('%Y-%m-%d %H:%M:%S')}"
    
    await update.message.reply_text(msg)


async def system_state_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current Titan system state."""
    state_manager = get_state_manager()
    info = state_manager.get_state_info()
    
    state = info["state"]
    can_trade = "🔒 No" if not info["can_trade"] else "🔓 Yes"
    is_critical = "🚨 CRITICAL" if info["is_critical"] else "✅ Normal"
    
    msg = f"🤖 TITAN SYSTEM STATE\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"State: *{state}*\n"
    msg += f"Can Trade: {can_trade}\n"
    msg += f"Status: {is_critical}\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    
    # Show recent transitions
    history = state_manager.get_transition_history(limit=3)
    if history:
        msg += "Recent Transitions:\n"
        for t in reversed(history):
            msg += f"  • {t.from_state.value} → {t.to_state.value}\n"
            msg += f"    {t.reason}\n"
            msg += f"    {t.timestamp.strftime('%H:%M:%S')}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def recovery_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent recovery sessions."""
    recovery_engine = get_recovery_engine()
    sessions = recovery_engine.get_recent_sessions(limit=5)
    
    if not sessions:
        await update.message.reply_text("✅ No recent recovery incidents.")
        return
    
    msg = "🔧 RECOVERY SESSIONS\n━━━━━━━━━━━━━━━━━━━━\n"
    
    for session in sessions:
        status = "✅ Resolved" if session.resolved else "⚠️ Active"
        escalated = " 🚨 ESCALATED" if session.escalated else ""
        
        msg += f"*{session.incident_id}*\n"
        msg += f"Issue: {session.issue}\n"
        msg += f"Status: {status}{escalated}\n"
        msg += f"Final: {session.final_state or 'Pending'}\n"
        msg += f"Duration: {(datetime.utcnow() - session.started_at).total_seconds():.0f}s\n"
        msg += f"Steps: {len(session.steps)}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def diagnostics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Full diagnostic report."""
    from datetime import datetime
    
    msg = "🔍 TITAN DIAGNOSTICS\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # State
    state_manager = get_state_manager()
    state_info = state_manager.get_state_info()
    msg += f"*STATE:* {state_info['state']}\n"
    msg += f"Can Trade: {'Yes' if state_info['can_trade'] else 'No'}\n\n"
    
    # Health
    health_monitor = get_health_monitor()
    health = health_monitor.get_current_health()
    if health:
        msg += f"*HEALTH:* {health.health_score}% ({health.overall_status.value})\n\n"
        
        msg += "*SUBSYSTEMS:*\n"
        for name, sub in health.subsystems.items():
            msg += f"  • {name}: {sub.status.value}\n"
        msg += "\n"
    
    # Recovery
    recovery_engine = get_recovery_engine()
    active = recovery_engine.get_active_sessions()
    msg += f"*ACTIVE INCIDENTS:* {len(active)}\n"
    
    # Rolling Performance
    learning = get_learning_engine()
    rolling = await learning.update_rolling_performance()
    msg += f"\n*ROLLING PERFORMANCE:*\n"
    msg += f"Last 20: {rolling.window_20['count']} trades, {rolling.window_20.get('win_rate', 0):.1f}% WR\n"
    msg += f"Last 50: {rolling.window_50['count']} trades, {rolling.window_50.get('win_rate', 0):.1f}% WR\n"
    msg += f"Last 100: {rolling.window_100['count']} trades, {rolling.window_100.get('win_rate', 0):.1f}% WR\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def status_command_op(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comprehensive status report."""
    from datetime import datetime
    
    state_manager = get_state_manager()
    health_monitor = get_health_monitor()
    learning = get_learning_engine()
    
    # Get stats
    rolling = await learning.update_rolling_performance()
    weekly = await learning.get_weekly_review(weeks_back=1)
    
    state_info = state_manager.get_state_info()
    health = health_monitor.get_current_health()
    
    msg = "📊 TITAN STATUS\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"State: *{state_info['state']}*\n"
    msg += f"Health: {health.health_score if health else 'N/A'}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*This Week:*\n"
    msg += f"Trades: {weekly.total_trades}\n"
    msg += f"Win Rate: {weekly.win_rate:.1f}%\n"
    msg += f"Expectancy: {weekly.expectancy:.2f}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Rolling:*\n"
    msg += f"Last 20: {rolling.window_20['count']} trades\n"
    msg += f"Streak: {rolling.consecutive_wins}W/{rolling.consecutive_losses}L\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


# ==================== LEARNING COMMANDS ====================

async def weekly_review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Weekly performance review."""
    user_id = update.effective_user.id
    
    learning = get_learning_engine()
    weekly = await learning.get_weekly_review(weeks_back=1)
    
    if weekly.total_trades == 0:
        await update.message.reply_text(
            "📊 WEEKLY REVIEW\n━━━━━━━━━━━━━━━━━━━━\n"
            "No completed trades this week.\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Start trading to see statistics."
        )
        return
    
    msg = "📊 WEEKLY REVIEW\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"Week: {weekly.week_start.strftime('%Y-%m-%d')} to {weekly.week_end.strftime('%Y-%m-%d')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Performance:*\n"
    msg += f"Total Trades: {weekly.total_trades}\n"
    msg += f"Wins: {weekly.wins} | Losses: {weekly.losses}\n"
    msg += f"Win Rate: {weekly.win_rate:.1f}%\n"
    msg += f"Expectancy: {weekly.expectancy:.2f}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Averages:*\n"
    msg += f"Avg Confidence: {weekly.avg_confidence:.1f}\n"
    msg += f"Avg ATR: {weekly.avg_atr:.2f}%\n"
    
    # By Regime
    if weekly.by_regime:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*By Regime:*\n"
        for regime, data in weekly.by_regime.items():
            msg += f"{regime}: {data['win_rate']:.1f}% ({data['total']} trades)\n"
    
    # By Setup
    if weekly.by_setup:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*By Setup:*\n"
        for setup, data in weekly.by_setup.items():
            setup_name = setup.replace('_', ' ')
            msg += f"{setup_name}: {data['win_rate']:.1f}% ({data['total']} trades)\n"
    
    # Pairs
    if weekly.by_pair:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"*Best Pair:* {weekly.best_pair}\n"
        msg += f"*Worst Pair:* {weekly.worst_pair}\n"
    
    # Streaks
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Streaks:*\n"
    msg += f"Best Win Streak: {weekly.best_streak}\n"
    msg += f"Worst Loss Streak: {weekly.worst_streak}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    logger.info(f"Weekly review generated by user {user_id}")


async def calibration_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show confidence calibration analysis."""
    learning = get_learning_engine()
    calibration = await learning.analyze_confidence_calibration()
    
    msg = "📈 CONFIDENCE CALIBRATION\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Does confidence predict outcomes?*\n\n"
    
    # Table
    ranges = [
        ("35-40", calibration.range_35_40),
        ("30-34", calibration.range_30_34),
        ("25-29", calibration.range_25_29),
        ("20-24", calibration.range_20_24),
    ]
    
    for range_label, data in ranges:
        total = data["total"]
        rate = data["rate"]
        bar = "█" * int(rate / 10) if total > 0 else "-"
        count_str = f"({total})" if total > 0 else ""
        msg += f"{range_label}: {rate:5.1f}% {bar} {count_str}\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Interpretation:*\n"
    msg += "Higher confidence = Higher win rate?\n"
    msg += "Use this to tune score thresholds."
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def feature_importance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show feature importance analysis."""
    learning = get_learning_engine()
    importance = await learning.analyze_feature_importance()
    
    msg = "📊 FEATURE IMPORTANCE\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Which factors predict wins?*\n\n"
    
    features = [
        ("Trend Alignment", importance.trend_alignment),
        ("Volume", importance.volume),
        ("ATR", importance.atr),
        ("MACD", importance.macd),
        ("Price Action", importance.price_action),
        ("News", importance.news),
    ]
    
    # Sort by importance
    features.sort(key=lambda x: x[1], reverse=True)
    
    for name, value in features:
        bar = "█" * int(value / 10) if value > 0 else "-"
        msg += f"{name:16s}: {value:5.1f}% {bar}\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Purpose:* Tune future scoring weights."
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain a specific signal decision."""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Usage: /explain <signal_id>\n"
            "Get the signal ID from /journal"
        )
        return
    
    try:
        signal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid signal ID. Use a number.")
        return
    
    learning = get_learning_engine()
    explanation = await learning.get_explanation(signal_id)
    
    if not explanation:
        await update.message.reply_text(f"❌ Signal {signal_id} not found.")
        return
    
    msg = f"📋 SIGNAL #{signal_id} EXPLANATION\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"*Time:* {explanation['timestamp']}\n"
    msg += f"*Pair:* {explanation['symbol']}\n"
    msg += f"*Signal:* {explanation['signal']}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Decision Factors:*\n"
    msg += f"Score: {explanation['score']}/40\n"
    msg += f"Regime: {explanation['regime']}\n"
    msg += f"Setup: {explanation['setup_type']}\n"
    
    # Score breakdown
    breakdown = explanation.get('score_breakdown', {})
    if breakdown:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*Score Breakdown:*\n"
        for key, value in breakdown.items():
            if key != 'reasons' and isinstance(value, (int, float)):
                msg += f"  {key}: {value}\n"
    
    # Outcome
    if explanation['outcome']:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "*Outcome:*\n"
        msg += f"Result: {explanation['outcome']}\n"
        if explanation.get('pnl_pct'):
            msg += f"P&L: {explanation['pnl_pct']:+.2f}%\n"
        if explanation.get('failure_type'):
            msg += f"Failure Type: {explanation['failure_type']}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def classify_failure_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Classify a losing trade (admin only)."""
    from core.user_manager import is_admin
    
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "ℹ️ Usage: /classify <signal_id> <failure_type>\n\n"
            "Failure types:\n"
            "• REGIME_MISMATCH\n"
            "• ENTRY_TOO_EARLY\n"
            "• ENTRY_TOO_LATE\n"
            "• VOLATILITY_SPIKE\n"
            "• LOW_VOLUME\n"
            "• NEWS_EVENT\n"
            "• STOP_HUNT\n"
            "• UNKNOWN"
        )
        return
    
    try:
        signal_id = int(context.args[0])
        failure_type = context.args[1].upper()
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments.")
        return
    
    valid_types = [
        FailureType.REGIME_MISMATCH, FailureType.ENTRY_TOO_EARLY,
        FailureType.ENTRY_TOO_LATE, FailureType.VOLATILITY_SPIKE,
        FailureType.LOW_VOLUME, FailureType.NEWS_EVENT,
        FailureType.STOP_HUNT, FailureType.UNKNOWN
    ]
    
    if failure_type not in valid_types:
        await update.message.reply_text(f"❌ Invalid failure type: {failure_type}")
        return
    
    learning = get_learning_engine()
    success = await learning.classify_failure(signal_id, failure_type)
    
    if success:
        await update.message.reply_text(f"✅ Signal {signal_id} classified as {failure_type}")
        logger.info(f"User {user_id} classified signal {signal_id} as {failure_type}")
    else:
        await update.message.reply_text(f"❌ Failed to classify signal {signal_id}")


async def learning_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current learning mode and recommended mode."""
    learning = get_learning_engine()
    
    mode_config = learning.get_mode_config()
    recommended = await learning.get_recommended_mode()
    
    emoji = {
        "CONSERVATIVE": "🛡️",
        "MODERATE": "⚖️",
        "AGGRESSIVE": "🚀",
        "PAPER_TESTING": "🧪",
        "RECOVERY": "🏥",
    }
    
    mode_emoji = emoji.get(mode_config['mode'], "⚙️")
    rec_emoji = emoji.get(recommended, "⚙️")
    
    msg = f"{mode_emoji} *LEARNING MODE: {mode_config['mode']}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📝 Reason: {mode_config['reason']}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "*Configuration:*\n"
    msg += f"Min Confidence: *{mode_config['min_confidence']}*\n"
    msg += f"Max Risk: *{mode_config['max_risk_percent']}%*\n"
    msg += f"Max Positions: *{mode_config['max_positions']}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🤖 Recommended: {rec_emoji} *{recommended}*\n"
    msg += "\n_Use /set_mode <name> to change mode_"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def set_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set learning mode manually (admin only)."""
    from core.user_manager import is_admin
    
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Usage: /set_mode <mode>\n\n"
            "Available modes:\n"
            "• CONSERVATIVE - 🛡️ High confidence, low risk\n"
            "• MODERATE - ⚖️ Balanced approach\n"
            "• AGGRESSIVE - 🚀 Lower confidence OK, higher risk\n"
            "• PAPER_TESTING - 🧪 For testing strategies\n"
            "• RECOVERY - 🏥 After losses, very conservative"
        )
        return
    
    mode = context.args[0].upper()
    valid_modes = ["CONSERVATIVE", "MODERATE", "AGGRESSIVE", "PAPER_TESTING", "RECOVERY"]
    
    if mode not in valid_modes:
        await update.message.reply_text(f"❌ Invalid mode: {mode}")
        return
    
    learning = get_learning_engine()
    success = await learning.set_mode(mode)
    
    if success:
        mode_config = learning.get_mode_config()
        await update.message.reply_text(
            f"✅ Learning mode set to *{mode}*\n"
            f"Min confidence: {mode_config['min_confidence']}\n"
            f"Max risk: {mode_config['max_risk_percent']}%"
        , parse_mode='Markdown')
        logger.info(f"User {user_id} changed learning mode to {mode}")
    else:
        await update.message.reply_text("❌ Failed to set mode")


def register_operations(application):
    """Register all operations commands."""
    # Operational commands
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("health_report", health_report_command))
    application.add_handler(CommandHandler("system_state", system_state_command))
    application.add_handler(CommandHandler("recovery", recovery_command))
    application.add_handler(CommandHandler("diagnostics", diagnostics_command))
    application.add_handler(CommandHandler("status", status_command_op))
    
    # Learning commands
    application.add_handler(CommandHandler("weekly_review", weekly_review_command))
    application.add_handler(CommandHandler("calibration", calibration_command))
    application.add_handler(CommandHandler("feature_importance", feature_importance_command))
    application.add_handler(CommandHandler("explain", explain_command))
    application.add_handler(CommandHandler("classify", classify_failure_command))
    application.add_handler(CommandHandler("learning_mode", learning_mode_command))
    application.add_handler(CommandHandler("set_mode", set_mode_command))
