"""
scheduler.py - WAVE 3C
Paper Trading Scheduler & Monitor with Circuit Breakers
Automatically checks positions, manages trading schedule, enforces safety limits.
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker for autonomous trading safety.
    Prevents catastrophic losses from consecutive failures.
    """
    
    def __init__(self):
        # Daily loss limits
        self.max_daily_loss_pct = 5.0  # 5% daily = pause
        self.max_weekly_loss_pct = 10.0  # 10% weekly = review
        
        # Consecutive loss limits
        self.max_consecutive_losses = 5  # 5 losses = pause
        self.warning_consecutive = 3     # 3 losses = warning
        
        # Tracking
        self._daily_loss = 0.0
        self._daily_loss_reset = datetime.utcnow()
        self._pause_until: Optional[datetime] = None
        
    def reset_daily(self):
        """Reset daily counters."""
        now = datetime.utcnow()
        if (now - self._daily_loss_reset).days >= 1:
            self._daily_loss = 0.0
            self._daily_loss_reset = now
            logger.info("Circuit breaker daily reset")
    
    def record_loss(self, loss_pct: float):
        """Record a loss."""
        self._daily_loss += abs(loss_pct)
        logger.info(f"Circuit breaker: Daily loss now {self._daily_loss:.2f}%")
        
    def can_trade(self, consecutive_losses: int = 0) -> tuple[bool, str]:
        """Check if trading is allowed."""
        # Check pause timeout
        if self._pause_until:
            if datetime.utcnow() < self._pause_until:
                remaining = (self._pause_until - datetime.utcnow()).total_seconds() / 60
                return False, f"Paused: {remaining:.0f} min remaining"
            else:
                # Pause expired
                self._pause_until = None
                logger.info("Circuit breaker pause expired")
        
        # Check daily loss
        self.reset_daily()
        if self._daily_loss >= self.max_daily_loss_pct:
            # Pause for 4 hours
            self._pause_until = datetime.utcnow() + timedelta(hours=4)
            return False, f"Daily loss limit hit: {self._daily_loss:.1f}% >= {self.max_daily_loss_pct}%"
        
        # Check consecutive losses
        if consecutive_losses >= self.max_consecutive_losses:
            # Pause for 24 hours
            self._pause_until = datetime.utcnow() + timedelta(hours=24)
            return False, f"Consecutive loss limit: {consecutive_losses} >= {self.max_consecutive_losses}"
        
        if consecutive_losses >= self.warning_consecutive:
            return True, f"WARNING: {consecutive_losses} consecutive losses"
        
        return True, "OK"
    
    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "daily_loss": self._daily_loss,
            "max_daily": self.max_daily_loss_pct,
            "consecutive_limit": self.max_consecutive_losses,
            "pause_until": self._pause_until.isoformat() if self._pause_until else None
        }


class TradingScheduler:
    """
    Manages trading schedule and position monitoring with circuit breakers.
    """
    
    def __init__(self):
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._trading_enabled = True
        self._circuit_breaker = CircuitBreaker()
        
        # Trading hours (UTC)
        self.trading_start = time(0, 0)   # 00:00 UTC
        self.trading_end = time(23, 59)   # 23:59 UTC
        
        # Check intervals
        self.position_check_interval = 60  # Check positions every 60 seconds
        self.health_check_interval = 300   # Health check every 5 minutes
    
    @property
    def circuit_breaker(self) -> CircuitBreaker:
        return self._circuit_breaker
    
    async def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Trading scheduler started with circuit breakers")
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Trading scheduler stopped")
    
    def enable_trading(self):
        """Enable trading."""
        self._trading_enabled = True
        logger.info("Trading enabled")
    
    def disable_trading(self):
        """Disable trading."""
        self._trading_enabled = False
        logger.info("Trading disabled")
    
    def is_trading_allowed(self, consecutive_losses: int = 0) -> tuple[bool, str]:
        """Check if trading is allowed based on schedule and circuit breakers."""
        # Check circuit breaker first
        cb_allowed, cb_reason = self._circuit_breaker.can_trade(consecutive_losses)
        if not cb_allowed:
            return False, f"Circuit breaker: {cb_reason}"
        
        if not self._trading_enabled:
            return False, "Trading disabled by administrator"

        # Check trading hours
        now = datetime.utcnow().time()
        in_hours = self.trading_start <= now <= self.trading_end
        
        if not in_hours:
            return False, "Outside trading hours"
        
        return True, "OK"
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_positions()
                await asyncio.sleep(self.position_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(self.position_check_interval)
    
    async def _check_positions(self):
        """Check all positions for SL/TP hits."""
        try:
            from broker.paper import get_paper_broker
            
            broker = get_paper_broker()
            closed = await broker.check_positions()
            
            if closed:
                for position in closed:
                    logger.info(f"Position closed: {position.pair} - {position.exit_reason.value}")
                    await self._notify_position_closed(position)
                    
        except Exception as e:
            logger.error(f"Position check error: {e}")
    
    async def _notify_position_closed(self, position):
        """Notify about closed position."""
        from core.state_manager import get_state_manager
        
        state = get_state_manager()
        
        # Log to audit
        from core.audit import log_event
        log_event(
            "INFO",
            f"Position closed: {position.pair}",
            context=f"P&L: ${position.pnl:.2f} | Reason: {position.exit_reason.value}"
        )
        
        # Check if we need to pause due to losses
        if position.pnl < 0:
            account = await get_paper_broker().get_account()
            
            if account.consecutive_losses >= 3:
                await state.set_state("SAFE_MODE")
                logger.warning(f"Entered SAFE_MODE: {account.consecutive_losses} consecutive losses")
            
            if account.consecutive_losses >= 5:
                await state.set_state("PAUSED")
                self.disable_trading()
                logger.critical("Trading paused: 5 consecutive losses")


# Global instance
_scheduler: Optional[TradingScheduler] = None


def get_scheduler() -> TradingScheduler:
    """Get scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TradingScheduler()
    return _scheduler


class SignalScheduler:
    """
    Schedules periodic signal generation.
    """
    
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.signal_interval = 3600  # Generate signals every hour
    
    async def start(self):
        """Start signal scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._signal_loop())
        logger.info("Signal scheduler started")
    
    async def stop(self):
        """Stop signal scheduler."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _signal_loop(self):
        """Signal generation loop."""
        while self._running:
            try:
                # Signal generation happens on-demand via commands
                # This loop could trigger periodic analysis
                await asyncio.sleep(self.signal_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Signal scheduler error: {e}")
                await asyncio.sleep(self.signal_interval)


# Global instance
_signal_scheduler: Optional[SignalScheduler] = None


def get_signal_scheduler() -> SignalScheduler:
    """Get signal scheduler instance."""
    global _signal_scheduler
    if _signal_scheduler is None:
        _signal_scheduler = SignalScheduler()
    return _signal_scheduler