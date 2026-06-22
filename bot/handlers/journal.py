"""
journal.py - TITAN Wave 2B
Journal and expectancy commands.
"""
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, CommandHandler, Application
)
from core.decision_journal import (
    get_recent_signals, get_signals_by_band
)
from core.expectancy_tracker import (
    calculate_expectancy, get_overall_stats
)

logger = logging.getLogger(__name__)

async def journal_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        signals = await get_recent_signals(10)
        if not signals:
            await update.message.reply_text(
                "📋 No signals yet.\n"
                "Use /signal BTCUSDT to generate one."
            )
            return
        lines = ["📋 Recent Signals", "━━━━━━━━━━━━━━━━━━━━"]
        for s in signals:
            emoji = ("🟢" if s['signal']=="LONG"
                    else "🔴" if s['signal']=="SHORT"
                    else "⚪")
            lines.append(
                f"{emoji} {s['symbol']} | "
                f"{s['score']}/40 | "
                f"{s['outcome']} | "
                f"{str(s['timestamp'])[:10]}"
            )
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Journal failed: {e}")
        await update.message.reply_text("❌ Journal unavailable.")

async def expectancy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        stats = await get_overall_stats()
        bands = await calculate_expectancy()
        lines = [
            "📊 Titan Expectancy Report",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Total Signals: {stats['total_signals']}",
            f"Completed: {stats['completed']}",
            f"Pending: {stats['pending']}",
            f"Win Rate: {stats['win_rate']}%",
            "━━━━━━━━━━━━━━━━━━━━",
            "By Confidence Band:",
        ]
        for band, data in bands.items():
            lines.append(
                f"  {band}: {data['win_rate']}% "
                f"({data['wins']}/{data['total']})"
            )
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append(
            "⚠️ Need 50+ signals for reliable data"
        )
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Expectancy failed: {e}")
        await update.message.reply_text(
            "❌ Expectancy data unavailable."
        )

def register_journal(app: Application):
    app.add_handler(
        CommandHandler("journal", journal_command)
    )
    app.add_handler(
        CommandHandler("expectancy", expectancy_command)
    )
