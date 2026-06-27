"""
interface.py - WAVE 3A
Broker Interface
Abstract interface for all broker implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional
from broker.models import Position, Account, ExecutionResult


class BrokerInterface(ABC):
    """
    Abstract broker interface.
    All broker implementations must implement this interface.
    
    Execution Layer
         ↓
    Broker Interface (this)
         ↓
    PaperBroker (current)
         ↓
    KrakenBroker (future)
         ↓
    BinanceBroker (future)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Broker name."""
        pass
    
    @property
    @abstractmethod
    def is_paper(self) -> bool:
        """True if paper trading."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connected."""
        pass
    
    # ==================== ACCOUNT ====================
    
    @abstractmethod
    async def get_account(self) -> Account:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        """Get available balance."""
        pass
    
    @abstractmethod
    async def update_balance(self, balance: float) -> bool:
        """Update account balance."""
        pass
    
    # ==================== POSITIONS ====================
    
    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    async def get_position(self, position_id: int) -> Optional[Position]:
        """Get position by ID."""
        pass
    
    @abstractmethod
    async def get_position_by_pair(self, pair: str) -> Optional[Position]:
        """Get open position for pair."""
        pass
    
    # ==================== EXECUTION ====================
    
    @abstractmethod
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
        Open a new position.
        
        Args:
            pair: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            quantity: Position size
            risk_percent: Risk percentage (default 2%)
            signal_id: Associated signal ID
            setup_type: Setup classification
            regime: Current market regime
            confidence: Confidence score
            
        Returns:
            ExecutionResult with success/failure
        """
        pass
    
    @abstractmethod
    async def close_position(
        self,
        position_id: int,
        exit_price: float,
        reason: str
    ) -> ExecutionResult:
        """
        Close an existing position.
        
        Args:
            position_id: Position ID
            exit_price: Exit price
            reason: Exit reason
            
        Returns:
            ExecutionResult
        """
        pass
    
    @abstractmethod
    async def modify_position(
        self,
        position_id: int,
        stop_loss: float = None,
        take_profit: float = None
    ) -> ExecutionResult:
        """
        Modify position SL/TP.
        
        Args:
            position_id: Position ID
            stop_loss: New stop loss
            take_profit: New take profit
            
        Returns:
            ExecutionResult
        """
        pass
    
    # ==================== MONITORING ====================
    
    @abstractmethod
    async def check_positions(self) -> list[Position]:
        """
        Check all positions for SL/TP hits.
        Returns list of positions that were closed.
        """
        pass
    
    @abstractmethod
    async def get_market_price(self, pair: str) -> float:
        """Get current market price for pair."""
        pass
    
    # ==================== UTILITY ====================
    
    @abstractmethod
    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float = 2.0
    ) -> float:
        """
        Calculate position size based on risk.
        
        Args:
            balance: Account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percent: Risk percentage
            
        Returns:
            Position quantity
        """
        pass
    
    @abstractmethod
    def calculate_risk(
        self,
        entry_price: float,
        stop_loss: float,
        quantity: float
    ) -> tuple[float, float]:
        """
        Calculate risk amount and percentage.
        
        Returns:
            (risk_amount, risk_percent)
        """
        pass
