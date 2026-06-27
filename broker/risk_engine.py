"""
risk_engine.py - WAVE 3B
Survival & Risk Engine
Position sizing, SL/TP calculation, risk validation.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """Risk configuration."""
    max_risk_percent: float = 2.0      # Max risk per trade (%)
    max_portfolio_exposure: float = 50.0  # Max total exposure (%)
    max_position_size: float = 10.0    # Max single position (%)
    min_risk_reward: float = 1.5       # Minimum R:R ratio
    max_positions: int = 3             # Max simultaneous positions
    stop_loss_atr_multiplier: float = 2.0  # SL = Entry - (ATR * multiplier)
    take_profit_atr_multiplier: float = 4.0  # TP = Entry + (ATR * multiplier)


class RiskEngine:
    """
    Risk management engine.
    Validates all trades against survival rules.
    """
    
    def __init__(self, config: RiskConfig = None):
        self.config = config or RiskConfig()
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float = None
    ) -> tuple[float, float]:
        """
        Calculate position size based on risk.
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percent: Risk percentage (default from config)
            
        Returns:
            (quantity, risk_amount)
        """
        if risk_percent is None:
            risk_percent = self.config.max_risk_percent
        
        risk_amount = account_balance * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0, 0
        
        quantity = risk_amount / price_risk
        actual_risk = price_risk * quantity
        
        return quantity, actual_risk
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        side: str,
        multiplier: float = None
    ) -> float:
        """
        Calculate stop loss based on ATR.
        
        Args:
            entry_price: Entry price
            atr: ATR value
            side: 'BUY' or 'SELL'
            multiplier: ATR multiplier (default from config)
            
        Returns:
            Stop loss price
        """
        if multiplier is None:
            multiplier = self.config.stop_loss_atr_multiplier
        
        sl_distance = atr * multiplier
        
        if side.upper() == "BUY":
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance
    
    def calculate_take_profit(
        self,
        entry_price: float,
        atr: float,
        side: str,
        multiplier: float = None,
        min_rr: float = None
    ) -> float:
        """
        Calculate take profit based on ATR and minimum R:R.
        
        Args:
            entry_price: Entry price
            atr: ATR value
            side: 'BUY' or 'SELL'
            multiplier: ATR multiplier (default from config)
            min_rr: Minimum risk:reward ratio
            
        Returns:
            Take profit price
        """
        if multiplier is None:
            multiplier = self.config.take_profit_atr_multiplier
        
        tp_distance = atr * multiplier
        
        if side.upper() == "BUY":
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance
    
    def validate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        side: str
    ) -> tuple[bool, float]:
        """
        Validate risk:reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            side: 'BUY' or 'SELL'
            
        Returns:
            (is_valid, rr_ratio)
        """
        risk = abs(entry_price - stop_loss)
        
        if side.upper() == "BUY":
            reward = abs(take_profit - entry_price)
        else:
            reward = abs(entry_price - take_profit)
        
        if risk == 0:
            return False, 0
        
        rr_ratio = reward / risk
        
        is_valid = rr_ratio >= self.config.min_risk_reward
        
        return is_valid, rr_ratio
    
    def validate_position_size(
        self,
        position_value: float,
        account_balance: float
    ) -> tuple[bool, str]:
        """
        Validate position size against limits.
        
        Args:
            position_value: Total position value
            account_balance: Account balance
            
        Returns:
            (is_valid, reason)
        """
        position_pct = (position_value / account_balance) * 100 if account_balance > 0 else 100
        
        if position_pct > self.config.max_position_size:
            return False, f"Position ({position_pct:.1f}%) exceeds max ({self.config.max_position_size}%)"
        
        return True, "OK"
    
    def validate_portfolio_exposure(
        self,
        total_exposure: float,
        new_position: float,
        account_balance: float
    ) -> tuple[bool, str]:
        """
        Validate total portfolio exposure.
        
        Args:
            total_exposure: Current total exposure
            new_position: New position value
            account_balance: Account balance
            
        Returns:
            (is_valid, reason)
        """
        new_total = total_exposure + new_position
        exposure_pct = (new_total / account_balance) * 100 if account_balance > 0 else 100
        
        if exposure_pct > self.config.max_portfolio_exposure:
            return False, f"Total exposure ({exposure_pct:.1f}%) exceeds max ({self.config.max_portfolio_exposure}%)"
        
        return True, "OK"
    
    def validate_trade(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        side: str,
        current_exposure: float = 0,
        open_positions: int = 0
    ) -> tuple[bool, str, dict]:
        """
        Full trade validation.
        
        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            side: 'BUY' or 'SELL'
            current_exposure: Current portfolio exposure
            open_positions: Number of open positions
            
        Returns:
            (is_valid, reason, trade_params)
        """
        # Calculate position
        quantity, risk_amount = self.calculate_position_size(
            account_balance, entry_price, stop_loss
        )
        
        position_value = entry_price * quantity
        
        # Check position limit
        if open_positions >= self.config.max_positions:
            return False, f"Max positions ({self.config.max_positions}) reached", {}
        
        # Validate position size
        valid, reason = self.validate_position_size(position_value, account_balance)
        if not valid:
            return False, reason, {}
        
        # Validate portfolio exposure
        valid, reason = self.validate_portfolio_exposure(
            current_exposure, position_value, account_balance
        )
        if not valid:
            return False, reason, {}
        
        # Validate risk:reward
        valid, rr_ratio = self.validate_risk_reward(
            entry_price, stop_loss, take_profit, side
        )
        if not valid:
            return False, f"R:R ({rr_ratio:.2f}) below minimum ({self.config.min_risk_reward})", {}
        
        return True, "OK", {
            "quantity": quantity,
            "risk_amount": risk_amount,
            "position_value": position_value,
            "risk_percent": (risk_amount / account_balance) * 100,
            "rr_ratio": rr_ratio
        }
    
    def get_max_risk(self, account_balance: float) -> float:
        """Get maximum risk amount for account."""
        return account_balance * (self.config.max_risk_percent / 100)


# Global instance
_risk_engine: Optional[RiskEngine] = None


def get_risk_engine() -> RiskEngine:
    """Get risk engine instance."""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine