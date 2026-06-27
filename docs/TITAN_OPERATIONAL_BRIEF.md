# TITAN OPERATIONAL BRIEF
## Survival First Trading Instructions

**Version:** 1.0  
**Date:** June 2026  
**Principle:** Survival > Large Profits

---

## Core Mandate

Titan's primary objective is **capital preservation**, not maximum returns.

A trader who survives with modest gains outperforms a trader who blows up chasing large profits.

---

## Capital Management Rules

### Position Sizing

| Rule | Value | Rationale |
|------|-------|-----------|
| Max Risk Per Trade | 2% | Survive losing streaks |
| Max Portfolio Exposure | 50% | Never be fully invested |
| Max Single Position | 10% | Diversify risk |
| Min Cash Reserve | 20% | Emergency buffer |

### Stop Loss Rules

| Condition | Stop Loss | Notes |
|-----------|-----------|-------|
| Default | ATR × 2 | Market-aware |
| Tight (volatility) | ATR × 1.5 | High VIX |
| Wide (trending) | ATR × 2.5 | Give room |

### Take Profit Rules

| Condition | Minimum TP | Target |
|-----------|-----------|--------|
| Minimum R:R | 1.5:1 | Non-negotiable |
| Target R:R | 2:1 | Preferred |
| Partial Exit | 50% at 1:1 | Lock profits |

---

## Signal Quality Filters

### Score Thresholds

| Regime | Min Score | Action |
|--------|-----------|--------|
| TRENDING_BULL | 24 | Long only |
| TRENDING_BEAR | 24 | Short only |
| RANGING | 30 | Higher bar |
| HIGH_VOLATILITY | 40 | Skip entirely |

### Market Conditions

```
IF ATR < 0.5%:
    → Skip (no movement, spread eats profit)

IF ATR > 5%:
    → Skip (extreme volatility, unpredictable)

IF Volume < MA20:
    → Reject signal

IF Major news event detected:
    → Delay entry 4 hours
```

### Time Filters

| Session | Weight | Action |
|---------|--------|--------|
| Asian (00:00-08:00 UTC) | 0.7× | Reduce size |
| London (08:00-16:00 UTC) | 1.0× | Normal |
| NY (13:00-21:00 UTC) | 1.2× | Normal |
| Overlap (13:00-16:00 UTC) | 1.5× | Full size |
| Weekend | 0.5× | Reduce significantly |

---

## Position Management Rules

### Entry

```
1. Wait for candle close confirmation
2. Verify 4H trend matches direction
3. Check no major news in next 4 hours
4. Confirm stop level below recent support
5. Execute only if all pass
```

### During Position

```
IF price moves 1% in our favor:
    → Move stop to breakeven

IF regime changes:
    → Reassess, tighten stop or exit

IF 3 hours pass without progress:
    → Review thesis, consider exit
```

### Exit Rules

```
EXIT IF ANY:
├── Stop loss hit
├── Take profit hit  
├── Regime changes to opposing
├── Opposing signal fires
├── News event contradicts thesis
└── 72 hours elapsed (time stop)
```

---

## Failure Response Protocol

### Consecutive Losses

```
3 CONSECUTIVE LOSSES:
├── Enter SAFE_MODE
├── Reduce position size 50%
├── Require confirmation for entries
└── Continue monitoring

5 CONSECUTIVE LOSSES:
├── STOP all new entries
├── Require human approval
└── Document in journal
```

### Drawdown Protocol

```
DRAWDOWN 5%:
└── Warning - monitor closely

DRAWDOWN 8%:
├── Reduce position size 50%
└── Review strategy

DRAWDOWN 10%:
├── STOP trading immediately
├── Generate incident report
└── Await human review
```

### System Failures

```
EXCHANGE UNAVAILABLE (> 5 min):
├── Stop new entries
├── Maintain existing positions
└── Alert admin

DATABASE LOCKED:
├── Retry 3 times
├── If persistent, disable trading
└── Alert admin

JOURNAL FAILURE:
├── Never execute trade without journal
└── Alert admin immediately
```

---

## Trade Cooldown Rules

### Same Pair
```
Minimum time between signals: 4 hours
Override requires: Admin approval
```

### Opposing Signal
```
IF LONG active AND SHORT signal fires:
    → Evaluate without closing LONG
    → Only close if SHORT confidence > LONG + 10
    → Document reasoning
```

---

## Survival Metrics

Titan tracks these constantly:

| Metric | Warning | Critical |
|--------|---------|----------|
| Win Rate (20 trades) | < 50% | < 40% |
| Expectancy | < 0.5% | < 0% |
| Max Drawdown | > 5% | > 8% |
| Consecutive Losses | 2 | 3 |
| ATR Volatility | < 0.3% | > 6% |

---

## Decision Hierarchy

When uncertain, Titan follows this order:

1. **Can I afford to lose 2%?**
2. **Does the regime support this direction?**
3. **Is the risk:reward at least 1.5:1?**
4. **Are market conditions favorable?**
5. **Is volume confirming?**
6. **Is time of day favorable?**
7. **Is there upcoming news risk?**
8. **Execute or skip**

---

## What Titan NEVER Does

```
❌ Averaging down
❌ Adding to losing position
❌ Trading against 4H trend
❌ Entering before candle close
❌ Ignoring stop loss
❌ Holding through news events
❌ Overriding risk rules
❌ Revenge trading
❌ Trading when tired/unwell
❌ Chasing losses
❌ Over-concentrating portfolio
❌ Executing without journal entry
```

---

## Weekly Review Triggers

Titan flags for review if:

```
├── Win rate drops > 10% vs previous week
├── Any single trade loses > 4%
├── Strategy decay detected
├── New regime pattern emerges
└── 3+ consecutive losses at any point
```

---

## Human Override

Admin can at any time:

```
/paper_stop     → Pause all trading
/paper_reset    → Reset portfolio (with reason)
/emergency_stop → Full system halt
```

---

## Remember

> **A 60% win rate with 1.5% wins beats a 40% win rate with 5% wins.**
> 
> **Stay in the game. There will always be another trade.**
> 
> **Survival is the only win condition that matters.**

---

**Titan follows these rules without exception.**

**Deviation requires explicit human authorization.**

---

*Document Version: 1.0 | Review: Monthly*
