"""
confidence_engine.py - TITAN Wave 2A
40-Point confidence scoring system.
Scores are hypotheses not proven edge.
All scores logged for future calibration.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

MAX_SCORE = 40
MIN_TRADEABLE = 26

def calculate_score(df: pd.DataFrame, regime: dict) -> dict:
    if df.empty or len(df) < 50:
        return {"total": 0, "breakdown": {}, "reasons": {}, "tradeable": False}

    scores = {}
    reasons = {}

    try:
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(min(200, len(df)-1)).mean()
        latest = df.iloc[-1]
        latest_close = close.iloc[-1]

        # Trend Alignment (12 pts)
        trend_score = 0
        if latest_close > ma20.iloc[-1]: trend_score += 4
        if ma20.iloc[-1] > ma50.iloc[-1]: trend_score += 4
        if latest_close > ma200.iloc[-1]: trend_score += 4
        scores['trend_alignment'] = min(trend_score, 12)
        reasons['trend_alignment'] = f"Price vs MAs: {trend_score}/12"

        # Price Action RSI (10 pts)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        if 40 <= rsi <= 60: pa_score = 10
        elif 35 <= rsi <= 65: pa_score = 7
        elif 30 <= rsi <= 70: pa_score = 4
        else: pa_score = 1
        scores['price_action'] = pa_score
        reasons['price_action'] = f"RSI: {round(rsi, 1)} → {pa_score}/10"

        # Volume (6 pts)
        vol_ma = volume.rolling(20).mean().iloc[-1]
        vol_ratio = latest['volume'] / vol_ma if vol_ma > 0 else 1
        if vol_ratio > 1.5: vol_score = 6
        elif vol_ratio > 1.2: vol_score = 4
        elif vol_ratio > 0.8: vol_score = 2
        else: vol_score = 0
        scores['volume'] = vol_score
        reasons['volume'] = f"Vol ratio: {round(vol_ratio, 2)} → {vol_score}/6"

        # MACD (4 pts)
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_score = 4 if macd_line.iloc[-1] > signal_line.iloc[-1] else 0
        scores['macd'] = macd_score
        reasons['macd'] = f"MACD cross: {macd_score}/4"

        # ATR (4 pts)
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': (high - close.shift()).abs(),
            'lc': (low - close.shift()).abs()
        }).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        atr_pct = (atr / latest_close) * 100
        if 0.5 <= atr_pct <= 2.0: atr_score = 4
        elif atr_pct < 0.5: atr_score = 1
        else: atr_score = 2
        scores['atr'] = atr_score
        reasons['atr'] = f"ATR%: {round(atr_pct, 2)} → {atr_score}/4"

        # News (4 pts) neutral default
        scores['news'] = 2
        reasons['news'] = "News: Neutral (2/4)"

        total = sum(scores.values())
        tradeable = total >= MIN_TRADEABLE

        return {
            "total": total,
            "max": MAX_SCORE,
            "breakdown": scores,
            "reasons": reasons,
            "tradeable": tradeable,
            "verdict": "TRADEABLE" if tradeable else "SKIP"
        }

    except Exception as e:
        logger.error(f"Confidence scoring failed: {e}")
        return {"total": 0, "breakdown": {}, "reasons": {}, "tradeable": False}
