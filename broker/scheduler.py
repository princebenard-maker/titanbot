"""
scheduler.py - WAVE 3C
Paper Trading Scheduler & Monitor
Automatically checks positions, manages trading schedule.
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional

logger = logging.getLogger(__name__)


class TradingScheduler:
    """
    Manages trading schedule and position monitoring.
    """
    
    def __init__(self):
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._trading_enabled = True
        
        # Trading hours (UTC)
        self.trading_start = time(0, 0)   # 00:00 UTC
        self.trading_end = time(23, 59)   # 23:59 UTC
        
        # Check intervals
        self.position_check_interval = 60  # Check positions every 60 seconds
        self.health_check_interval = 300   # Health check every 5 minutes
    
    async def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Trading scheduler started")
    
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
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed based on schedule."""
        if not self._trading_enabled:
            return False
        
        # Check trading hours
        now = datetime.utcnow().time()
        in_hours = self.trading_start <= now <= self.trading_end
        
        return in_hours
    
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