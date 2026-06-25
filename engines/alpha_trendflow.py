"""
alpha_trendflow.py - TITAN Wave 2A/2B
Alpha TrendFlow v1.1
Generates LONG/SHORT/WAIT only.
Never executes trades.
"""
import pandas as pd
import logging
from engines.regime_classifier import classify_regime, MarketRegime
from engines.confidence_engine import calculate_score
from config.constants import (
    SETUP_TREND_CONTINUATION,
    SETUP_TREND_PULLBACK,
    SETUP_BREAKOUT_CONFIRMATION
)

logger = logging.getLogger(__name__)

class Signal:
    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"


def classify_setup(df_4h, df_1h, df_15m, direction: str) -> str:
    """
    Classify the trade setup type based on multi-timeframe analysis.
    
    TREND_CONTINUATION: Price making new highs/lows in established trend direction
    TREND_PULLBACK: Price retracing to key moving average or support/resistance
    BREAKOUT_CONFIRMATION: Price breaking key level with volume confirmation
    """
    if df_4h.empty or df_1h.empty:
        return SETUP_TREND_CONTINUATION
    
    try:
        close_4h = df_4h['close']
        close_1h = df_1h['close']
        
        # Calculate moving averages
        ma20_4h = close_4h.rolling(20).mean().iloc[-1]
        ma50_4h = close_4h.rolling(50).mean().iloc[-1]
        ma20_1h = close_1h.rolling(20).mean().iloc[-1]
        
        latest_4h = close_4h.iloc[-1]
        high_4h_20 = close_4h.tail(20).max()
        low_4h_20 = close_4h.tail(20).min()
        
        # For LONG signals
        if direction == Signal.LONG:
            # Check if making new highs (continuation)
            if latest_4h >= high_4h_20 * 0.99:
                return SETUP_TREND_CONTINUATION
            
            # Check if price pulled back to MA (pullback)
            if latest_4h < ma20_4h or (ma20_1h > close_1h.iloc[-1] and close_1h.iloc[-1] > ma20_1h * 0.98):
                return SETUP_TREND_PULLBACK
            
            # Check for breakout from range
            range_size = high_4h_20 - low_4h_20
            mid_range = low_4h_20 + (range_size * 0.5)
            if latest_4h > mid_range and latest_4h < high_4h_20 * 0.98:
                return SETUP_BREAKOUT_CONFIRMATION
            
            return SETUP_TREND_CONTINUATION
        
        # For SHORT signals
        elif direction == Signal.SHORT:
            # Check if making new lows (continuation)
            if latest_4h <= low_4h_20 * 1.01:
                return SETUP_TREND_CONTINUATION
            
            # Check if price pulled back to MA (pullback)
            if latest_4h > ma20_4h or (ma20_1h < close_1h.iloc[-1] and close_1h.iloc[-1] < ma20_1h * 0.98):
                return SETUP_TREND_PULLBACK
            
            # Check for breakout from range
            range_size = high_4h_20 - low_4h_20
            mid_range = low_4h_20 + (range_size * 0.5)
            if latest_4h < mid_range and latest_4h > low_4h_20 * 1.02:
                return SETUP_BREAKOUT_CONFIRMATION
            
            return SETUP_TREND_CONTINUATION
        
        return SETUP_TREND_CONTINUATION
        
    except Exception as e:
        logger.warning(f"Setup classification error: {e}")
        return SETUP_TREND_CONTINUATION

def generate_signal(df_4h, df_1h, df_15m) -> dict:
    if df_4h.empty or df_1h.empty or df_15m.empty:
        return {"signal": Signal.WAIT, "reason": "Insufficient data", "score": 0}
    try:
        regime = classify_regime(df_4h)
        if regime['regime'] == MarketRegime.HIGH_VOLATILITY:
            return {"signal": Signal.WAIT, "regime": regime['regime'],
                    "reason": "High volatility - no trades", "score": 0}

        close_4h = df_4h['close']
        ma20 = close_4h.rolling(20).mean().iloc[-1]
        ma50 = close_4h.rolling(50).mean().iloc[-1]
        latest = close_4h.iloc[-1]
        bullish = latest > ma20 > ma50
        bearish = latest < ma20 < ma50

        if not bullish and not bearish:
            return {"signal": Signal.WAIT, "regime": regime['regime'],
                    "reason": "No clear 4H trend", "score": 0}

        delta_1h = df_1h['close'].diff()
        gain_1h = delta_1h.clip(lower=0).rolling(14).mean()
        loss_1h = (-delta_1h.clip(upper=0)).rolling(14).mean()
        rsi_1h = (100 - (100 / (1 + gain_1h/loss_1h))).iloc[-1]
        momentum_ok = 35 <= rsi_1h <= 65

        delta_15m = df_15m['close'].diff()
        gain_15m = delta_15m.clip(lower=0).rolling(14).mean()
        loss_15m = (-delta_15m.clip(upper=0)).rolling(14).mean()
        rsi_15m = (100 - (100/(1+gain_15m/loss_15m))).iloc[-1]

        score_data = calculate_score(df_4h, regime)
        total_score = score_data['total']

        if total_score < 26:
            return {"signal": Signal.WAIT, "regime": regime['regime'],
                    "reason": f"Score too low: {total_score}/40", "score": total_score}

        if bullish and momentum_ok and rsi_15m < 60:
            direction = Signal.LONG
            reason = "Bullish 4H + momentum ok + entry timing"
        elif bearish and momentum_ok and rsi_15m > 40:
            direction = Signal.SHORT
            reason = "Bearish 4H + momentum ok + entry timing"
        else:
            direction = Signal.WAIT
            reason = "Conditions not fully aligned"

        # Classify setup type for actionable signals
        setup_type = classify_setup(df_4h, df_1h, df_15m, direction) if direction != Signal.WAIT else "N/A"

        return {
            "signal": direction,
            "regime": regime['regime'],
            "score": total_score,
            "score_breakdown": score_data['breakdown'],
            "reasons": score_data['reasons'],
            "reason": reason,
            "tradeable": score_data['tradeable'],
            "setup_type": setup_type
        }
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        return {"signal": Signal.WAIT, "reason": str(e), "score": 0}
