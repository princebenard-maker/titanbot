"""
alpha_trendflow.py - TITAN Wave 2A
Alpha TrendFlow v1.0 - LOCKED.
Generates LONG/SHORT/WAIT only.
Never executes trades.
"""
import pandas as pd
import logging
from engines.regime_classifier import classify_regime, MarketRegime
from engines.confidence_engine import calculate_score

logger = logging.getLogger(__name__)

class Signal:
    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"

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

        return {
            "signal": direction,
            "regime": regime['regime'],
            "score": total_score,
            "score_breakdown": score_data['breakdown'],
            "reasons": score_data['reasons'],
            "reason": reason,
            "tradeable": score_data['tradeable']
        }
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        return {"signal": Signal.WAIT, "reason": str(e), "score": 0}
