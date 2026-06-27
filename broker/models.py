"""
models.py - WAVE 3A
Paper Broker Data Models
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PositionSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOPPED = "STOPPED"
    TARGETED = "TARGETED"


class ExitReason(Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    MANUAL = "MANUAL"
    TIME_LIMIT = "TIME_LIMIT"
    EMERGENCY = "EMERGENCY"
    REGIME_CHANGE = "REGIME_CHANGE"
    OPPOSING_SIGNAL = "OPPOSING_SIGNAL"


class TradeStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Position:
    """Trading position model."""
    id: Optional[int] = None
    trade_id: Optional[str] = None
    signal_id: Optional[int] = None
    pair: str = ""
    side: PositionSide = PositionSide.BUY
    status: PositionStatus = PositionStatus.OPEN
    
    # Entry
    entry_price: float = 0.0
    quantity: float = 0.0
    entry_time: datetime = field(default_factory=datetime.utcnow)
    
    # Exit
    exit_price: float = 0.0
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    
    # Risk
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_percent: float = 2.0
    risk_amount: float = 0.0
    
    # Calculated
    position_size: float = 0.0
    
    # P&L
    pnl: float = 0.0
    pnl_percent: float = 0.0
    r_multiple: float = 0.0
    
    # Setup info
    setup_type: str = "N/A"
    regime: str = "UNKNOWN"
    confidence: int = 0
    
    # Duration
    duration_hours: float = 0.0
    
    def calculate_pnl(self, current_price: float = None) -> float:
        """Calculate current P&L."""
        if current_price is None:
            current_price = self.exit_price if self.exit_price else self.entry_price
        
        if self.side == PositionSide.BUY:
            self.pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.pnl = (self.entry_price - current_price) * self.quantity
        
        if self.entry_price > 0:
            self.pnl_percent = ((current_price - self.entry_price) / self.entry_price) * 100 if self.side == PositionSide.BUY else ((self.entry_price - current_price) / self.entry_price) * 100
        
        # R multiple: profit/loss relative to risk
        if self.risk_amount > 0:
            self.r_multiple = self.pnl / self.risk_amount
        
        return self.pnl
    
    def calculate_duration(self) -> float:
        """Calculate position duration in hours."""
        end = self.exit_time or datetime.utcnow()
        delta = end - self.entry_time
        self.duration_hours = delta.total_seconds() / 3600
        return self.duration_hours
    
    def check_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss hit."""
        if self.side == PositionSide.BUY:
            return current_price <= self.stop_loss
        else:
            return current_price >= self.stop_loss
    
    def check_take_profit(self, current_price: float) -> bool:
        """Check if take profit hit."""
        if self.side == PositionSide.BUY:
            return current_price >= self.take_profit
        else:
            return current_price <= self.take_profit


@dataclass
class Account:
    """Paper trading account."""
    id: int = 1
    broker: str = "PAPER"
    
    # Balances
    initial_balance: float = 10.0
    balance: float = 10.0
    equity: float = 10.0
    available_balance: float = 10.0
    reserved: float = 0.0
    
    # P&L
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    
    # Calculated
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    
    # Drawdown
    peak_equity: float = 10.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    
    # Streaks
    current_streak: int = 0
    max_win_streak: int = 0
    max_loss_streak: int = 0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    
    # Risk limits
    daily_loss: float = 0.0
    weekly_loss: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_stats(self):
        """Calculate account statistics."""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        # Calculate avg win/loss from trades
        if self.winning_trades > 0:
            total_wins = 0
            # Would need to calculate from trades
            self.avg_win = total_wins / self.winning_trades
        
        # Profit factor
        if self.avg_loss != 0:
            self.profit_factor = abs(self.avg_win / self.avg_loss) if self.avg_loss != 0 else 0
        
        # Expectancy
        if self.total_trades > 0:
            wr = self.win_rate / 100
            self.expectancy = (wr * self.avg_win) - ((1 - wr) * abs(self.avg_loss))
        
        # Drawdown
        self.equity = self.balance + self.unrealized_pnl
        self.current_drawdown = ((self.peak_equity - self.equity) / self.peak_equity) * 100 if self.peak_equity > 0 else 0
        
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        
        if self.current_drawdown > self.max_drawdown:
            self.max_drawdown = self.current_drawdown
        
        self.updated_at = datetime.utcnow()
    
    def can_open_position(self, risk_amount: float) -> tuple[bool, str]:
        """Check if can open new position."""
        # Check balance
        if self.available_balance < risk_amount:
            return False, f"Insufficient balance: ${self.available_balance:.2f} < ${risk_amount:.2f}"
        
        # Check drawdown
        if self.current_drawdown >= 15:
            return False, "Maximum drawdown (15%) exceeded"
        
        # Check consecutive losses
        if self.consecutive_losses >= 5:
            return False, "Maximum consecutive losses (5) reached"
        
        # Check daily loss
        if self.daily_loss >= 5:
            return False, "Maximum daily loss (5%) exceeded"
        
        # Check weekly loss
        if self.weekly_loss >= 10:
            return False, "Maximum weekly loss (10%) exceeded"
        
        return True, "OK"
    
    def update_after_trade(self, trade: Position):
        """Update account after trade closes."""
        self.total_trades += 1
        self.realized_pnl += trade.pnl
        self.balance += trade.pnl
        
        if trade.pnl > 0:
            self.winning_trades += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.max_win_streak = max(self.max_win_streak, self.consecutive_wins)
        elif trade.pnl < 0:
            self.losing_trades += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.max_loss_streak = max(self.max_loss_streak, self.consecutive_losses)
        else:
            self.breakeven_trades += 1
        
        self.calculate_stats()


@dataclass
class ExecutionResult:
    """Result of trade execution."""
    success: bool
    order_id: Optional[str] = None
    position_id: Optional[int] = None
    message: str = ""
    filled_price: float = 0.0
    filled_quantity: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RejectionReason:
    """Reason for trade rejection."""
    code: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
