"""
regime_classifier.py - TITAN Wave 2A
Classifies current market regime.
Uses ATR and MA slope only. No ML.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class MarketRegime:
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"

def classify_regime(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 20:
        return {
            "regime": MarketRegime.RANGING,
            "confidence": 0,
            "atr_pct": 0,
            "note": "Insufficient data"
        }
    try:
        close = df['close']
        high = df['high']
        low = df['low']
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': (high - close.shift()).abs(),
            'lc': (low - close.shift()).abs()
        }).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        ma_fast = close.rolling(20).mean()
        ma_slow = close.rolling(50).mean()
        ma_slope = ma_fast.diff(5).iloc[-1]
        latest_close = close.iloc[-1]
        latest_ma_fast = ma_fast.iloc[-1]
        latest_ma_slow = ma_slow.iloc[-1]
        atr_pct = (atr / latest_close) * 100
        ma_diff = ((latest_ma_fast - latest_ma_slow) / latest_ma_slow) * 100

        if atr_pct > 3.0:
            return {"regime": MarketRegime.HIGH_VOLATILITY,
                    "confidence": min(int(atr_pct * 20), 100),
                    "atr_pct": round(atr_pct, 2),
                    "note": "High volatility - avoid trading"}
        if ma_slope > 0 and ma_diff > 0.5:
            return {"regime": MarketRegime.TRENDING_BULL,
                    "confidence": min(int(abs(ma_slope)*10 + ma_diff*10), 100),
                    "atr_pct": round(atr_pct, 2),
                    "note": "Bullish trend confirmed"}
        if ma_slope < 0 and ma_diff < -0.5:
            return {"regime": MarketRegime.TRENDING_BEAR,
                    "confidence": min(int(abs(ma_slope)*10 + abs(ma_diff)*10), 100),
                    "atr_pct": round(atr_pct, 2),
                    "note": "Bearish trend confirmed"}
        if atr_pct < 0.8:
            return {"regime": MarketRegime.LOW_VOLATILITY,
                    "confidence": 60,
                    "atr_pct": round(atr_pct, 2),
                    "note": "Low volatility - weak signals"}
        return {"regime": MarketRegime.RANGING,
                "confidence": 50,
                "atr_pct": round(atr_pct, 2),
                "note": "Ranging market - be cautious"}
    except Exception as e:
        logger.error(f"Regime classification failed: {e}")
        return {"regime": MarketRegime.RANGING, "confidence": 0,
                "atr_pct": 0, "note": str(e)}
