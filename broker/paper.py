"""
paper.py - WAVE 3A
Paper Broker Implementation
Internal paper trading broker.
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional
import json

from broker.interface import BrokerInterface
from broker.models import (
    Position, Account, ExecutionResult, PositionStatus, PositionSide,
    ExitReason, TradeStatus
)

logger = logging.getLogger(__name__)


class PaperBroker(BrokerInterface):
    """
    Paper trading broker.
    Simulates execution without real exchange.
    """
    
    # Configuration
    INITIAL_BALANCE = 10.0
    SLIPPAGE = 0.002  # 0.20%
    COMMISSION = 0.001  # 0.10%
    
    def __init__(self):
        self._connected = False
        self._account: Optional[Account] = None
        self._positions: dict[int, Position] = {}
        self._position_counter = 0
        self._lock = asyncio.Lock()
    
    @property
    def name(self) -> str:
        return "PAPER"
    
    @property
    def is_paper(self) -> bool:
        return True
    
    async def connect(self) -> bool:
        """Connect to paper broker (load account)."""
        async with self._lock:
            try:
                # Load account from database or create new
                self._account = await self._load_account()
                self._connected = True
                logger.info(f"Paper broker connected. Balance: ${self._account.balance:.2f}")
                return True
            except Exception as e:
                logger.error(f"Paper broker connection failed: {e}")
                return False
    
    async def disconnect(self) -> bool:
        """Disconnect from paper broker."""
        async with self._lock:
            try:
                await self._save_account()
                self._connected = False
                logger.info("Paper broker disconnected")
                return True
            except Exception as e:
                logger.error(f"Paper broker disconnect failed: {e}")
                return False
    
    async def is_connected(self) -> bool:
        return self._connected
    
    # ==================== ACCOUNT ====================
    
    async def get_account(self) -> Account:
        """Get account information."""
        if not self._account:
            self._account = await self._load_account()
        self._account.calculate_stats()
        return self._account
    
    async def get_balance(self) -> float:
        """Get available balance."""
        account = await self.get_account()
        return account.available_balance
    
    async def update_balance(self, balance: float) -> bool:
        """Update account balance."""
        async with self._lock:
            account = await self.get_account()
            account.balance = balance
            account.equity = balance + account.unrealized_pnl
            await self._save_account()
            return True
    
    # ==================== POSITIONS ====================
    
    async def get_positions(self) -> list[Position]:
        """Get all open positions."""
        async with self._lock:
            return [p for p in self._positions.values() if p.status == PositionStatus.OPEN]
    
    async def get_position(self, position_id: int) -> Optional[Position]:
        """Get position by ID."""
        return self._positions.get(position_id)
    
    async def get_position_by_pair(self, pair: str) -> Optional[Position]:
        """Get open position for pair."""
        for position in self._positions.values():
            if position.pair == pair and position.status == PositionStatus.OPEN:
                return position
        return None
    
    # ==================== EXECUTION ====================
    
    async def open_position(
        self,
        pair: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        risk_percent: float = 2.0,
        signal_id: Optional[int] = None,
        setup_type: str = "N/A",
        regime: str = "UNKNOWN",
        confidence: int = 0
    ) -> ExecutionResult:
        """
        Open a new paper position.
        """
        async with self._lock:
            # Check if position already exists for pair
            existing = await self.get_position_by_pair(pair)
            if existing:
                return ExecutionResult(
                    success=False,
                    message=f"Position already exists for {pair}"
                )
            
            # Calculate risk
            risk_amount = abs(entry_price - stop_loss) * quantity
            
            # Check account
            account = await self.get_account()
            can_open, reason = account.can_open_position(risk_amount)
            if not can_open:
                await self._log_rejection(pair, side, reason)
                return ExecutionResult(success=False, message=reason)
            
            # Apply slippage to entry
            filled_price = entry_price * (1 + self.SLIPPAGE) if side == "BUY" else entry_price * (1 - self.SLIPPAGE)
            
            # Apply commission
            commission = filled_price * quantity * self.COMMISSION
            
            # Create position
            self._position_counter += 1
            position = Position(
                id=self._position_counter,
                trade_id=str(uuid.uuid4())[:8].upper(),
                signal_id=signal_id,
                pair=pair,
                side=PositionSide.BUY if side == "BUY" else PositionSide.SELL,
                status=PositionStatus.OPEN,
                entry_price=filled_price,
                quantity=quantity,
                entry_time=datetime.utcnow(),
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_percent=risk_percent,
                risk_amount=risk_amount,
                position_size=filled_price * quantity,
                setup_type=setup_type,
                regime=regime,
                confidence=confidence
            )
            
            # Update account
            account.available_balance -= (position.position_size + commission)
            account.reserved += risk_amount
            account.calculate_stats()
            
            # Save
            self._positions[position.id] = position
            await self._save_account()
            await self._save_position(position)
            await self._log_trade(position, "OPEN")
            
            logger.info(f"Paper position opened: {pair} {side} @ {filled_price:.2f} Qty: {quantity}")
            
            return ExecutionResult(
                success=True,
                order_id=position.trade_id,
                position_id=position.id,
                message=f"Position opened: {pair}",
                filled_price=filled_price,
                filled_quantity=quantity,
                slippage=self.SLIPPAGE * 100,
                commission=commission
            )
    
    async def close_position(
        self,
        position_id: int,
        exit_price: float,
        reason: str
    ) -> ExecutionResult:
        """Close an existing position."""
        async with self._lock:
            position = self._positions.get(position_id)
            if not position:
                return ExecutionResult(success=False, message="Position not found")
            
            if position.status != PositionStatus.OPEN:
                return ExecutionResult(success=False, message="Position already closed")
            
            # Apply slippage
            filled_price = exit_price * (1 - self.SLIPPAGE) if position.side == PositionSide.BUY else exit_price * (1 + self.SLIPPAGE)
            
            # Apply commission
            commission = filled_price * position.quantity * self.COMMISSION
            
            # Calculate P&L
            if position.side == PositionSide.BUY:
                position.pnl = (filled_price - position.entry_price) * position.quantity
            else:
                position.pnl = (position.entry_price - filled_price) * position.quantity
            
            position.pnl -= commission
            position.pnl_percent = (position.pnl / position.position_size) * 100 if position.position_size > 0 else 0
            position.r_multiple = position.pnl / position.risk_amount if position.risk_amount > 0 else 0
            
            # Update position
            position.exit_price = filled_price
            position.exit_time = datetime.utcnow()
            position.status = PositionStatus.CLOSED
            position.calculate_duration()
            
            # Map reason
            reason_map = {
                "manual": ExitReason.MANUAL,
                "stop_loss": ExitReason.STOP_LOSS,
                "take_profit": ExitReason.TAKE_PROFIT,
                "emergency": ExitReason.EMERGENCY,
            }
            position.exit_reason = reason_map.get(reason.lower(), ExitReason.MANUAL)
            
            # Update account
            account = await self.get_account()
            account.balance += position.pnl
            account.available_balance += position.position_size + commission
            account.reserved -= position.risk_amount
            account.update_after_trade(position)
            
            # Save
            await self._save_account()
            await self._save_position(position)
            await self._log_trade(position, "CLOSE")
            
            logger.info(f"Paper position closed: {position.pair} P&L: ${position.pnl:.2f} ({position.pnl_percent:.1f}%) Reason: {reason}")
            
            return ExecutionResult(
                success=True,
                position_id=position.id,
                message=f"Position closed: {position.pair}",
                filled_price=filled_price,
                commission=commission
            )
    
    async def modify_position(
        self,
        position_id: int,
        stop_loss: float = None,
        take_profit: float = None
    ) -> ExecutionResult:
        """Modify position SL/TP."""
        position = self._positions.get(position_id)
        if not position:
            return ExecutionResult(success=False, message="Position not found")
        
        if stop_loss:
            position.stop_loss = stop_loss
        if take_profit:
            position.take_profit = take_profit
        
        await self._save_position(position)
        logger.info(f"Position modified: {position.pair} SL: {position.stop_loss} TP: {position.take_profit}")
        
        return ExecutionResult(success=True, position_id=position.id, message="Position modified")
    
    # ==================== MONITORING ====================
    
    async def check_positions(self) -> list[Position]:
        """
        Check all positions for SL/TP hits.
        Returns list of closed positions.
        """
        closed_positions = []
        
        async with self._lock:
            for position in self._positions.values():
                if position.status != PositionStatus.OPEN:
                    continue
                
                # Get current price
                current_price = await self.get_market_price(position.pair)
                
                # Check SL
                if position.check_stop_loss(current_price):
                    await self.close_position(position.id, current_price, "stop_loss")
                    closed_positions.append(position)
                    continue
                
                # Check TP
                if position.check_take_profit(current_price):
                    await self.close_position(position.id, current_price, "take_profit")
                    closed_positions.append(position)
                    continue
                
                # Update unrealized P&L
                position.calculate_pnl(current_price)
        
        return closed_positions
    
    async def get_market_price(self, pair: str) -> float:
        """Get current market price (from exchange)."""
        from core.exchange import get_market_price
        return await get_market_price(pair)
    
    # ==================== UTILITY ====================
    
    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float = 2.0
    ) -> float:
        """Calculate position size based on risk."""
        risk_amount = balance * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
        
        quantity = risk_amount / price_diff
        return quantity
    
    def calculate_risk(
        self,
        entry_price: float,
        stop_loss: float,
        quantity: float
    ) -> tuple[float, float]:
        """Calculate risk amount and percentage."""
        risk_amount = abs(entry_price - stop_loss) * quantity
        risk_percent = (risk_amount / (entry_price * quantity)) * 100 if entry_price * quantity > 0 else 0
        return risk_amount, risk_percent
    
    # ==================== PERSISTENCE ====================
    
    async def _load_account(self) -> Account:
        """Load account from database."""
        from db.database import execute_read_one
        
        row = await execute_read_one("SELECT * FROM paper_account WHERE id = 1")
        
        if row:
            account = Account(
                id=row['id'],
                broker=row.get('broker', 'PAPER'),
                initial_balance=row['initial_balance'],
                balance=row['balance'],
                equity=row.get('equity', row['balance']),
                available_balance=row.get('available_balance', row['balance']),
                reserved=row.get('reserved', 0),
                realized_pnl=row.get('realized_pnl', 0),
                peak_equity=row.get('peak_equity', row['balance']),
                max_drawdown=row.get('max_drawdown', 0),
                consecutive_wins=row.get('consecutive_wins', 0),
                consecutive_losses=row.get('consecutive_losses', 0),
            )
        else:
            account = Account(broker="PAPER", initial_balance=self.INITIAL_BALANCE)
            await self._save_account(account)
        
        return account
    
    async def _save_account(self, account: Account = None):
        """Save account to database."""
        from db.database import execute_write
        
        if not account:
            account = self._account
        
        await execute_write(
            """INSERT OR REPLACE INTO paper_account
               (id, broker, initial_balance, balance, equity, available_balance, reserved,
                realized_pnl, peak_equity, max_drawdown, consecutive_wins, consecutive_losses,
                total_trades, winning_trades, losing_trades, win_rate, profit_factor, expectancy,
                updated_at)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (account.broker, account.initial_balance, account.balance, account.equity,
             account.available_balance, account.reserved, account.realized_pnl,
             account.peak_equity, account.max_drawdown, account.consecutive_wins,
             account.consecutive_losses, account.total_trades, account.winning_trades,
             account.losing_trades, account.win_rate, account.profit_factor,
             account.expectancy, datetime.utcnow().isoformat())
        )
    
    async def _load_positions(self):
        """Load positions from database."""
        from db.database import execute_read
        
        rows = await execute_read("SELECT * FROM paper_positions WHERE status = 'OPEN'")
        
        for row in rows:
            position = Position(
                id=row['id'],
                pair=row['pair'],
                side=PositionSide.BUY if row['side'] == 'BUY' else PositionSide.SELL,
                status=PositionStatus.OPEN,
                entry_price=row['entry_price'],
                quantity=row['quantity'],
                stop_loss=row['stop_loss'],
                take_profit=row['take_profit'],
                risk_amount=row.get('risk_amount', 0),
                position_size=row.get('position_size', 0),
                setup_type=row.get('setup_type', 'N/A'),
                regime=row.get('regime', 'UNKNOWN'),
                confidence=row.get('confidence', 0),
            )
            self._positions[position.id] = position
            self._position_counter = max(self._position_counter, position.id)
    
    async def _save_position(self, position: Position):
        """Save position to database."""
        from db.database import execute_write
        
        await execute_write(
            """INSERT OR REPLACE INTO paper_positions
               (id, trade_id, signal_id, pair, side, status, entry_price, quantity,
                entry_time, exit_price, exit_time, exit_reason, stop_loss, take_profit,
                risk_percent, risk_amount, position_size, pnl, pnl_percent, r_multiple,
                setup_type, regime, confidence, duration_hours)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (position.id, position.trade_id, position.signal_id, position.pair,
             position.side.value, position.status.value, position.entry_price,
             position.quantity, position.entry_time.isoformat(),
             position.exit_price, position.exit_time.isoformat() if position.exit_time else None,
             position.exit_reason.value if position.exit_reason else None,
             position.stop_loss, position.take_profit, position.risk_percent,
             position.risk_amount, position.position_size, position.pnl, position.pnl_percent,
             position.r_multiple, position.setup_type, position.regime,
             position.confidence, position.duration_hours)
        )
    
    async def _log_trade(self, position: Position, action: str):
        """Log trade to audit."""
        from core.audit import log_event
        
        log_event(
            "INFO",
            f"Paper {action}: {position.pair} {position.side.value} @ {position.entry_price}",
            context=f"P&L: ${position.pnl:.2f} | R: {position.r_multiple:.2f}"
        )
    
    async def _log_rejection(self, pair: str, side: str, reason: str):
        """Log trade rejection."""
        from core.audit import log_event
        log_event("WARNING", f"Paper trade rejected: {pair} {side}", context=reason)
    
    # ==================== RESET ====================
    
    async def reset_account(self) -> bool:
        """Reset paper account to initial state."""
        async with self._lock:
            self._account = Account(broker="PAPER", initial_balance=self.INITIAL_BALANCE)
            self._positions.clear()
            self._position_counter = 0
            
            # Clear database
            from db.database import execute_write
            await execute_write("DELETE FROM paper_positions")
            await execute_write("DELETE FROM paper_account WHERE id = 1")
            
            # Create new account
            await self._save_account()
            
            from core.audit import log_event
            log_event("INFO", "Paper account reset", context=f"Balance: ${self.INITIAL_BALANCE}")
            
            logger.info(f"Paper account reset. Balance: ${self.INITIAL_BALANCE}")
            return True


# Global instance
_paper_broker: Optional[PaperBroker] = None


def get_paper_broker() -> PaperBroker:
    """Get paper broker singleton."""
    global _paper_broker
    if _paper_broker is None:
        _paper_broker = PaperBroker()
    return _paper_broker
