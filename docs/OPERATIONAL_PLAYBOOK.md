# TITAN OPERATIONAL PLAYBOOK
## Wave 2C/2D - Operations Layer Documentation

**Version:** 1.0 | **Status:** Production Ready

---

## System States

| State | Can Trade | Can Analyze |
|-------|-----------|------------|
| BOOTING | ❌ | ❌ |
| READY | ❌ | ✅ |
| ANALYZING | ❌ | ✅ |
| PAPER_TRADING | ✅ | ✅ |
| SAFE_MODE | ⚠️ | ✅ |
| RECOVERING | ❌ | ⚠️ |
| PAUSED | ❌ | ❌ |
| ERROR | ❌ | ❌ |
| SHUTDOWN | ❌ | ❌ |

## Health Monitoring

| Score | Status | Action |
|-------|---------|--------|
| 80-100% | ✅ HEALTHY | Continue |
| 60-79% | ⚠️ WARNING | Investigate |
| 40-59% | 🚨 CRITICAL | Pause trading |
| 0-39% | 🚨 EMERGENCY | Disable, alert |

## Recovery Matrix

| Failure | Detection | Recovery | Final State |
|---------|-----------|----------|-------------|
| Exchange timeout | 10s timeout | Retry 3x + backoff | PAUSED |
| Database lock | Lock error | Retry + rollback | JOURNALING_DISABLED |
| Missing candles | < required | Reject signal | SIGNAL_REJECTED |
| 3 consecutive losses | 3x LOSS | Enter SAFE_MODE | SAFE_MODE |
| 5 consecutive losses | 5x LOSS | Pause + approval | REQUIRES_APPROVAL |
| Health < 40% | Score calc | Disable + alert | EMERGENCY |

## Commands

### Operational
- /health - Quick status
- /health_report - Full report
- /system_state - Current state
- /recovery - Recent sessions
- /diagnostics - Full diagnostics

### Learning
- /weekly_review - Week stats
- /calibration - Confidence analysis
- /feature_importance - Factor analysis
- /explain <id> - Signal explanation

### Admin
- /classify <id> <type> - Classify failure

## Core Principle

Titan should never guess, never hide failures. Titan should either:
1. Continue safely
2. Recover safely
3. Stop safely
