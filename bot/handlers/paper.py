"""
paper.py - WAVE 3A
Paper Trading Commands
"""
import logging
import telegram
from telegram import Update
from telegram.ext import ContextTypes

from broker.paper import get_paper_broker
from broker.account import get_account_manager
from bot.handlers.admin import is_admin

logger = logging.getLogger(__name__)


async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display paper account information."""
    try:
        broker = get_paper_broker()
        account = await broker.get_account()
        manager = get_account_manager(broker)
        
        await update.message.reply_text(manager.format_account_summary(account))
        
    except Exception as e:
        logger.error(f"Account command error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display open positions."""
    try:
        broker = get_paper_broker()
        positions = await broker.get_positions()
        manager = get_account_manager(broker)
        
        await update.message.reply_text(manager.format_positions_list(positions))
        
    except Exception as e:
        logger.error(f"Positions command error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display recent completed trades."""
    try:
        from db.database import execute_read
        
        limit = 10
        if context.args and context.args[0].isdigit():
            limit = min(int(context.args[0]), 50)
        
        rows = await execute_read(
            """SELECT * FROM paper_positions 
               WHERE status != 'OPEN' 
               ORDER BY exit_time DESC LIMIT ?""",
            (limit,)
        )
        
        if not rows:
            await update.message.reply_text("📭 No completed trades yet.")
            return
        
        lines = ["📜 TRADE HISTORY", "━━━━━━━━━━━━━━━━━━━━"]
        
        for row in rows:
            emoji = "🟢" if row['pnl'] >= 0 else "🔴"
            duration = f"{row['duration_hours']:.1f}h" if row['duration_hours'] else "N/A"
            
            lines.append(f"{emoji} {row['pair']} {row['side']}")
            lines.append(f"   Entry: ${row['entry_price']:.2f} → Exit: ${row['exit_price']:.2f}")
            lines.append(f"   P&L: ${row['pnl']:.2f} ({row['pnl_percent']:+.1f}%) R: {row['r_multiple']:+.2f}")
            lines.append(f"   Duration: {duration} | Exit: {row['exit_reason']}")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        await update.message.reply_text("\n".join(lines))
        
    except Exception as e:
        logger.error(f"History command error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def paper_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display paper trading report."""
    try:
        from db.database import execute_read
        
        broker = get_paper_broker()
        account = await broker.get_account()
        
        # Get recent trades for stats
        trades = await execute_read(
            """SELECT * FROM paper_positions 
               WHERE status != 'OPEN' 
               ORDER BY created_at DESC LIMIT 100"""
        )
        
        if trades:
            wins = [t for t in trades if t['pnl'] > 0]
            losses = [t for t in trades if t['pnl'] < 0]
            
            avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
            avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
            
            largest_win = max(t['pnl'] for t in trades) if trades else 0
            largest_loss = min(t['pnl'] for t in trades) if trades else 0
            
            # Setup performance
            setup_stats = {}
            for t in trades:
                setup = t.get('setup_type', 'N/A')
                if setup not in setup_stats:
                    setup_stats[setup] = {'count': 0, 'wins': 0, 'pnl': 0}
                setup_stats[setup]['count'] += 1
                if t['pnl'] > 0:
                    setup_stats[setup]['wins'] += 1
                setup_stats[setup]['pnl'] += t['pnl']
        else:
            wins, losses = [], []
            avg_win = avg_loss = largest_win = largest_loss = 0
            setup_stats = {}
        
        # Format report
        pnl_emoji = "🟢" if account.realized_pnl >= 0 else "🔴"
        
        lines = [
            "📊 PAPER TRADING REPORT",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Broker: {account.broker}",
            f"Current Balance: ${account.balance:.2f}",
            f"{pnl_emoji} Total P&L: ${account.realized_pnl:+.2f}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Total Trades: {len(trades)}",
            f"Win Rate: {account.win_rate:.1f}%",
            f"Profit Factor: {account.profit_factor:.2f}",
            f"Expectancy: ${account.expectancy:.2f}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Largest Win: ${largest_win:.2f}",
            f"Largest Loss: ${largest_loss:.2f}",
            f"Avg Win: ${avg_win:.2f}",
            f"Avg Loss: ${avg_loss:.2f}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Max Drawdown: {account.max_drawdown:.1f}%",
            f"Current Drawdown: {account.current_drawdown:.1f}%",
            f"Peak Equity: ${account.peak_equity:.2f}",
        ]
        
        # Setup performance
        if setup_stats:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("📈 SETUP PERFORMANCE")
            for setup, stats in sorted(setup_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
                wr = (stats['wins'] / stats['count'] * 100) if stats['count'] > 0 else 0
                lines.append(f"  {setup}: {stats['count']} trades, {wr:.0f}% WR, ${stats['pnl']:+.2f}")
        
        await update.message.reply_text("\n".join(lines))
        
    except Exception as e:
        logger.error(f"Paper report error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def paper_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset paper account (admin only)."""
    try:
        # Check admin
        if not await is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only.")
            return
        
        broker = get_paper_broker()
        success = await broker.reset_account()
        
        if success:
            await update.message.reply_text("✅ Paper account reset. Balance: $10.00")
        else:
            await update.message.reply_text("❌ Reset failed.")
        
    except Exception as e:
        logger.error(f"Paper reset error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def broker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display current broker information."""
    try:
        broker = get_paper_broker()
        
        status = "🟢 Connected" if await broker.is_connected() else "🔴 Disconnected"
        
        lines = [
            "🏦 BROKER STATUS",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Current Broker: {broker.name}",
            f"Type: {'PAPER (Simulation)' if broker.is_paper else 'LIVE'}",
            f"Status: {status}",
            "━━━━━━━━━━━━━━━━━━━━",
            "Available Brokers:",
            "• PAPER - Internal simulation",
            "• KRAKEN - Live (future)",
            "• BINANCE - Live (future)",
        ]
        
        await update.message.reply_text("\n".join(lines))
        
    except Exception as e:
        logger.error(f"Broker command error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


def register_paper(app):
    """Register paper trading commands."""
    from telegram.ext import CommandHandler
    
    app.add_handler(CommandHandler("account", account_command))
    app.add_handler(CommandHandler("positions", positions_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("paper_report", paper_report_command))
    app.add_handler(CommandHandler("paper_reset", paper_reset_command))
    app.add_handler(CommandHandler("broker", broker_command))
    
    logger.info("Paper trading commands registered.")