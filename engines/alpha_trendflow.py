"""
alpha_trendflow.py - TITAN Wave 2A
Alpha TrendFlow v1.0 signal engine.
LOCKED. Do not modify without data evidence.
Generates LONG/SHORT/WAIT signals only.
Never executes trades. Never touches money.
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

def generate_signal(df_4h: pd.DataFrame, df_1h: pd.DataFrame, df_15m: pd.DataFrame) -> dict:
    if df_4h.empty or df_1h.empty or df_15m.empty:
        return {"signal": Signal.WAIT, "reason": "Insufficient data", "score": 0}

    try:
        # Step 1: Regime check
        regime = classify_regime(df_4h)

        if regime['regime'] == MarketRegime.HIGH_VOLATILITY:
            return {
                "signal": Signal.WAIT,
                "regime": regime['regime'],
                "reason": "High volatility — no trades",
                "score": 0
            }

        # Step 2: 4H trend
        close_4h = df_4h['close']
        ma20_4h = close_4h.rolling(20).mean().iloc[-1]
        ma50_4h = close_4h.rolling(50).mean().iloc[-1]
        latest_4h = close_4h.iloc[-1]

        bullish_4h = latest_4h > ma20_4h > ma50_4h
        bearish_4h = latest_4h < ma20_4h < ma50_4h

        if not bullish_4h and not bearish_4h:
            return {
                "signal": Signal.WAIT,
                "regime": regime['regime'],
                "reason": "No clear 4H trend",
                "score": 0
            }

        # Step 3: 1H RSI momentum
        close_1h = df_1h['close']
        delta_1h = close_1h.diff()
        gain_1h = delta_1h.clip(lower=0).rolling(14).mean()
        loss_1h = (-delta_1h.clip(upper=0)).rolling(14).mean()
        rsi_1h = (100 - (100 / (1 + gain_1h/loss_1h))).iloc[-1]
        momentum_ok = 35 <= rsi_1h <= 65

        # Step 4: 15M entry timing
        close_15m = df_15m['close']
        delta_15m = close_15m.diff()
        gain_15m = delta_15m.clip(lower=0).rolling(14).mean()
        loss_15m = (-delta_15m.clip(upper=0)).rolling(14).mean()
        rsi_15m = (100 - (100 / (1 + gain_15m/loss_15m))).iloc[-1]

        # Step 5: Confidence score
        score_data = calculate_score(df_4h, regime)
        total_score = score_data['total']

        if total_score < 26:
            return {
                "signal": Signal.WAIT,
                "regime": regime['regime'],
                "reason": f"Score too low: {total_score}/40",
                "score": total_score
            }

        # Step 6: Generate signal
        if bullish_4h and momentum_ok and rsi_15m < 60:
            direction = Signal.LONG
            reason = "Bullish 4H + momentum ok + entry timing"
        elif bearish_4h and momentum_ok and rsi_15m > 40:
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
