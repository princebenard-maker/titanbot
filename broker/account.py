"""
account.py - WAVE 3A
Paper Account Management
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from broker.models import Account

logger = logging.getLogger(__name__)


class PaperAccountManager:
    """
    Manages paper trading account.
    """
    
    # Survival limits
    MAX_DAILY_LOSS_PCT = 5.0
    MAX_WEEKLY_LOSS_PCT = 10.0
    MAX_DRAWDOWN_PCT = 15.0
    MAX_CONSECUTIVE_LOSSES = 5
    
    def __init__(self, broker):
        self.broker = broker
        self._daily_reset_time = self._get_daily_reset_time()
        self._weekly_reset_time = self._get_weekly_reset_time()
    
    def _get_daily_reset_time(self) -> datetime:
        """Get daily loss reset time (midnight UTC)."""
        now = datetime.utcnow()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _get_weekly_reset_time(self) -> datetime:
        """Get weekly loss reset time (Monday midnight UTC)."""
        now = datetime.utcnow()
        days_since_monday = now.weekday()
        monday = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return monday - timedelta(days=days_since_monday)
    
    async def check_survival_limits(self) -> tuple[bool, str]:
        """
        Check if survival limits are triggered.
        
        Returns:
            (can_trade, reason)
        """
        account = await self.broker.get_account()
        
        # Check drawdown
        if account.current_drawdown >= self.MAX_DRAWDOWN_PCT:
            return False, f"Maximum drawdown ({self.MAX_DRAWDOWN_PCT}%) exceeded"
        
        # Check consecutive losses
        if account.consecutive_losses >= self.MAX_CONSECUTIVE_LOSSES:
            return False, f"Maximum consecutive losses ({self.MAX_CONSECUTIVE_LOSSES}) reached"
        
        # Check daily loss
        if account.daily_loss >= self.MAX_DAILY_LOSS_PCT:
            return False, f"Maximum daily loss ({self.MAX_DAILY_LOSS_PCT}%) exceeded"
        
        # Check weekly loss
        if account.weekly_loss >= self.MAX_WEEKLY_LOSS_PCT:
            return False, f"Maximum weekly loss ({self.MAX_WEEKLY_LOSS_PCT}%) exceeded"
        
        return True, "OK"
    
    async def record_daily_loss(self, loss_pct: float):
        """Record daily loss."""
        account = await self.broker.get_account()
        account.daily_loss += loss_pct
        await self.broker.update_balance(account.balance)
    
    async def reset_daily_loss(self):
        """Reset daily loss tracker."""
        account = await self.broker.get_account()
        account.daily_loss = 0.0
        await self.broker.update_balance(account.balance)
    
    async def reset_weekly_loss(self):
        """Reset weekly loss tracker."""
        account = await self.broker.get_account()
        account.weekly_loss = 0.0
        await self.broker.update_balance(account.balance)
    
    def format_account_summary(self, account: Account) -> str:
        """Format account summary for display."""
        emoji = "✅" if account.balance >= account.initial_balance else "⚠️"
        
        lines = [
            f"{emoji} PAPER ACCOUNT",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Broker: {account.broker}",
            f"Balance: ${account.balance:.2f}",
            f"Equity: ${account.equity:.2f}",
            f"P&L: ${account.realized_pnl:+.2f} ({account.realized_pnl/account.initial_balance*100:+.1f}%)",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Trades: {account.total_trades}",
            f"Win Rate: {account.win_rate:.1f}%",
            f"Profit Factor: {account.profit_factor:.2f}",
            f"Expectancy: ${account.expectancy:.2f}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Drawdown: {account.current_drawdown:.1f}%",
            f"Peak Equity: ${account.peak_equity:.2f}",
            f"Win Streak: {account.max_win_streak}",
            f"Loss Streak: {account.max_loss_streak}",
        ]
        
        return "\n".join(lines)
    
    def format_positions_list(self, positions: list) -> str:
        """Format positions list for display."""
        if not positions:
            return "📭 No open positions"
        
        lines = ["📊 OPEN POSITIONS", "━━━━━━━━━━━━━━━━━━━━"]
        
        for pos in positions:
            emoji = "🟢" if pos.side.value == "BUY" else "🔴"
            pnl_emoji = "🟢" if pos.pnl >= 0 else "🔴"
            
            lines.append(f"{emoji} {pos.pair}")
            lines.append(f"   Entry: ${pos.entry_price:.2f}")
            lines.append(f"   SL: ${pos.stop_loss:.2f} | TP: ${pos.take_profit:.2f}")
            lines.append(f"   {pnl_emoji} P&L: ${pos.pnl:.2f} ({pos.pnl_percent:+.1f}%)")
            lines.append(f"   R: {pos.r_multiple:+.2f}")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)


# Global instance
_account_manager: Optional[PaperAccountManager] = None


def get_account_manager(broker) -> PaperAccountManager:
    """Get account manager."""
    global _account_manager
    if _account_manager is None:
        _account_manager = PaperAccountManager(broker)
    return _account_manager
