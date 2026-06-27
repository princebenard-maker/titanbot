# TITAN — MARKET PATTERNS & STRUCTURE GUIDE
## Documentation of Known Trends and Patterns

**Version:** 1.0  
**Date:** June 2026  
**Purpose:** Document market patterns for integration into Titan's analysis

> ⚠️ **NOTE:** These patterns exist. Whether they constitute an "edge" requires validation through backtesting (Wave 2E) and paper trading (Wave 3).

---

## PATTERNS ARE NOT EDGES

**Pattern:** Something that exists in markets.  
**Edge:** A pattern that, when traded consistently, produces positive expectancy.

Every pattern below must be:
1. ✅ Defined clearly
2. 📊 Validated with historical data
3. 📈 Tested in paper trading
4. 📉 Proven to have positive expectancy

**Until validated, these are hypotheses.**

---

## TREND PATTERNS

### 1. Trend Continuation

**Description:** Price making higher highs (LONG) or lower lows (SHORT) in an established trend.

**Characteristics:**
```
LONG: Higher highs + Higher lows + Price above 4H MA20
SHORT: Lower lows + Lower highs + Price below 4H MA20
```

**Entry:**
- Pullback to MA20 or recent support (LONG)
- Bounce off MA20 with momentum confirmation

**Stop:**
- Below recent swing low (LONG)
- Above recent swing high (SHORT)

**Validates With:**
- 4H trend aligned
- Volume increasing on continuation
- RSI between 40-70 (not overbought/oversold)

**Historical Performance:** To be validated

---

### 2. Trend Reversal

**Description:** Trend exhaustion leading to reversal.

**LONG Reversal Signs:**
```
- Price testing major support
- Hidden divergence on RSI
- Hammer/candlestick reversal patterns
- Volume spike on bounce
- MA20 flattening or turning up
```

**SHORT Reversal Signs:**
```
- Price testing major resistance
- Hidden divergence on RSI
- Shooting star/evening star
- Volume spike on rejection
- MA20 flattening or turning down
```

**High Risk:** Counter-trend trading. Requires strong confirmation.

---

### 3. Range Bound / Consolidation

**Description:** Price oscillating between support and resistance.

**Characteristics:**
```
- Price between two horizontal levels
- Lower ATR (compression)
- Lower volume
- MA20 flat/oscillating
```

**Strategy:**
```
- LONG at support
- SHORT at resistance
- Stop: Beyond the range
- Target: Opposite side of range
```

**Warning:** Breakouts happen. Always respect range breaks.

---

## MOMENTUM PATTERNS

### 4. RSI Divergence

**Description:** Price making new highs/lows while RSI fails to confirm.

**Bullish Divergence (LONG):**
```
- Price: Lower low
- RSI: Higher low
- Signal: Momentum shifting up
```

**Bearish Divergence (SHORT):**
```
- Price: Higher high
- RSI: Lower high
- Signal: Momentum shifting down
```

**Confirmation Required:**
- Divergence + candle close + volume

---

### 5. MACD Cross

**Description:** MACD line crossing signal line.

**Bullish Cross (LONG):**
```
- MACD below 0, crosses above signal
- Histogram turning positive
- Histogram expanding
```

**Bearish Cross (SHORT):**
```
- MACD above 0, crosses below signal
- Histogram turning negative
- Histogram expanding
```

**Best Used With:**
- Trend confirmation (MACD aligns with 4H trend)
- Not useful in ranging markets

---

### 6. RSI Mean Reversion

**Description:** RSI reaching extremes then reverting.

**Oversold (LONG):**
```
- RSI < 30 on 1H or 4H
- Price bouncing from support
- Next candle confirms
```

**Overbought (SHORT):**
```
- RSI > 70 on 1H or 4H
- Price rejected at resistance
- Next candle confirms
```

**Warning:** In strong trends, RSI can stay extreme. Use with trend filter.

---

## VOLUME PATTERNS

### 7. Volume Spike Breakout

**Description:** Volume spike confirming breakout.

**Characteristics:**
```
- Volume > 2x 20-period average
- Price closing near high/low
- Follow-through volume next candles
```

**Long Entry:**
```
- Break above resistance on high volume
- Retest of breakout level
- Entry on retest bounce
```

**Short Entry:**
```
- Break below support on high volume
- Retest of breakdown level
- Entry on retest rejection
```

---

### 8. Low Volume Consolidation

**Description:** Low volume before big move.

**Characteristics:**
```
- ATR dropping (volatility compression)
- Volume below average
- Price consolidating
- Often before breakout
```

**Strategy:**
```
- Identify consolidation zone
- Wait for volume expansion
- Trade in direction of breakout
- Don't predict which way
```

---

## STRUCTURE PATTERNS

### 9. Support and Resistance

**Description:** Price levels where buying/selling pressure exists.

**Support (LONG Zone):**
```
- Previous lows
- Round numbers
- 50%, 61.8% fib retracements
- EMA zones
```

**Resistance (SHORT Zone):**
```
- Previous highs
- All-time highs
- 50%, 61.8% fib retracements
- EMA zones
```

**Trading:**
```
- LONG: Buy from support, sell near resistance
- SHORT: Sell into resistance, buy back from support
```

---

### 10. Break of Structure (BOS)

**Description:** Price breaking key structure level.

**Bullish BOS:**
```
- Higher high broken
- New high confirmed
- Look for pullback entry
```

**Bearish BOS:**
```
- Lower low broken
- New low confirmed
- Look for bounce entry
```

**Higher Probability When:**
- Multiple timeframes agree
- Volume confirms
- Clean break (no wicks through)

---

### 11. Fair Value Gap (FVG)

**Description:** Gaps in price action (visible on lower TF).

**Bullish FVG:**
```
- Candle 1: Bearish candle
- Candle 2: Gap up (doesn't touch candle 1)
- Candle 3: Price returns to fill gap
- FILL = Buying opportunity
```

**Bearish FVG:**
```
- Candle 1: Bullish candle
- Candle 2: Gap down (doesn't touch candle 1)
- Candle 3: Price returns to fill gap
- FILL = Selling opportunity
```

---

## TIME-BASED PATTERNS

### 12. Session Volatility

**Description:** Different sessions have different characteristics.

| Session | Volatility | Trendiness | Best For |
|---------|------------|------------|----------|
| Asian (00:00-08:00 UTC) | Low | Range-bound | Range trading |
| London (08:00-12:00 UTC) | Medium | Trending | Breakouts |
| NY Open (13:00-16:00 UTC) | High | Trending | Momentum |
| NY Close (16:00-21:00 UTC) | Medium | Mixed | Scalping |
| Weekend | Very Low | Sideways | Skip |

**Implication:** Same signal in NY Open vs Asian has different probability.

---

### 13. Day of Week

**Description:** Certain days have different characteristics.

| Day | Character | Notes |
|-----|-----------|-------|
| Monday | Mixed | Often continuation of Friday |
| Tuesday | Trending | Higher volume |
| Wednesday | Trending | Mid-week momentum |
| Thursday | Mixed | Positioning day |
| Friday | Range-bound | Light volume, reversals |
| Weekend | Very Slow | Avoid |

---

## REGIME-SPECIFIC PATTERNS

### 14. Trending Market

**Best Setups:**
```
1. Trend Continuation Pullback
   - Price retraces to MA20
   - RSI showing strength (not oversold)
   - Volume on continuation

2. Momentum Breakout
   - Price compressing
   - Volume building
   - MACD strengthening

3. Higher TF Trend Confirmation
   - 4H: TRENDING_BULL
   - 1H: Pullback entry
```

---

### 15. Ranging Market

**Best Setups:**
```
1. Range Boundary Bounce
   - Price at support = LONG
   - Price at resistance = SHORT

2. Double Bottom/Top
   - Two tests of level
   - Volume on second test
   - Break of neckline entry

3. Mean Reversion
   - RSI extreme
   - Bounce expected
```

---

### 16. High Volatility

**⚠️ AVOID or REDUCE SIZE**

**Characteristics:**
```
- ATR > 5%
- Wide candles
- Unpredictable moves
- News events likely
```

**If Trading:**
```
- Wider stops (ATR × 3)
- Smaller size
- Quick exits
- Avoid entries during volatility spike
```

---

## ENTRY CONFIRMATION CHECKLIST

Before entering ANY trade:

```
1. REGIME CHECK
   [ ] 4H regime supports direction
   [ ] Not in HIGH_VOLATILITY

2. TREND CHECK
   [ ] 4H trend aligned
   [ ] Price above/below MA20

3. MOMENTUM CHECK
   [ ] RSI not extreme (30-70)
   [ ] MACD aligned

4. VOLUME CHECK
   [ ] Volume confirming move
   [ ] Not in low-volume consolidation breakout

5. STRUCTURE CHECK
   [ ] Support/resistance respected
   [ ] No major level nearby

6. TIME CHECK
   [ ] Good session (avoid Asian for momentum)
   [ ] No major news

7. ATR CHECK
   [ ] ATR > 0.5% (not dead)
   [ ] ATR < 5% (not crazy)

8. SCORE CHECK
   [ ] Score meets regime threshold

ALL PASS = ENTER
ANY FAIL = SKIP or REDUCE SIZE
```

---

## VALIDATION TRACKER

This table tracks which patterns have been validated.

| Pattern | Status | Win Rate | Sample Size | Notes |
|---------|--------|----------|-------------|-------|
| Trend Continuation | 🔲 To Test | - | - | |
| Trend Reversal | 🔲 To Test | - | - | High risk |
| Range Bound | 🔲 To Test | - | - | |
| RSI Divergence | 🔲 To Test | - | - | |
| MACD Cross | 🔲 To Test | - | - | |
| Volume Spike Breakout | 🔲 To Test | - | - | |
| FVG | 🔲 To Test | - | - | |
| Session Timing | 🔲 To Test | - | - | |

---

## DEFINITION OF EDGE

For a pattern to become part of Titan's EDGE:

```
1. Historical Validation
   - Backtest on 1+ years of data
   - Win rate > 50%
   - Positive expectancy

2. Statistical Significance
   - p-value < 0.05
   - Sample size > 100 trades
   - Consistent across market conditions

3. Paper Trading Validation
   - 21 days / 100 trades
   - Win rate > 55%
   - Max drawdown < 10%

ALL THREE = EDGE CONFIRMED
```

---

## IMPLEMENTATION IN TITAN

### Current State:
- ✅ Pattern awareness in signal generation
- ✅ Multi-timeframe analysis
- ✅ Volume consideration
- ✅ Regime awareness

### To Be Added:
- [ ] Pattern recognition in alpha_trendflow
- [ ] Score weighting by pattern type
- [ ] Pattern-specific entry rules
- [ ] Historical validation (Wave 2E)
- [ ] Pattern success tracking

---

*This document is a living reference. Update as patterns are validated.*
