# TITAN TRADING INTELLIGENCE PLATFORM
## Technical Specification Document (TSD-001)

**Version:** 1.0  
**Date:** June 2026  
**Status:** APPROVED FOR IMPLEMENTATION  
**Classification:** Internal Engineering Document

---

## Document Purpose

This document provides the complete engineering specification for Titan Trading Intelligence Platform from Wave 2C through Wave 4.

**Read Time:** 60 minutes  
**Implementation Duration:** 8-12 weeks  
**Team:** 1-2 engineers

---

# TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Wave 2C: Learning Engine](#wave-2c--learning-engine)
4. [Wave 2D: News Intelligence](#wave-2d--news-intelligence)
5. [Wave 2E: Historical Replay](#wave-2e--historical-replay)
6. [Wave 3: Paper Trading](#wave-3--paper-trading)
7. [Wave 4: Live Trading](#wave-4--live-trading)
8. [Health Manual](#health-manual)
9. [Command Interface](#command-interface)
10. [Implementation Checklists](#implementation-checklists)

---

# EXECUTIVE SUMMARY

## Current State (Post-Wave 2B)

| Component | Status |
|-----------|--------|
| Telegram Bot | ✅ Operational |
| Authentication | ✅ Operational |
| Market Data (CCXT) | ✅ Operational |
| Signal Generation | ✅ Operational |
| Decision Journal | ✅ Operational |
| Admin Controls | ✅ Operational |
| Health Monitoring | ✅ Implemented |
| Recovery Engine | ✅ Implemented |
| State Manager | ✅ Implemented |

## Completed Waves

- **Wave 1:** Foundation ✅
- **Wave 2A:** Market Intelligence ✅
- **Wave 2B:** Truth Engine ✅

## Remaining Waves

| Wave | Name | Status |
|------|------|--------|
| Wave 2C | Learning Engine | PENDING |
| Wave 2D | News Intelligence | PENDING |
| Wave 2E | Historical Replay | PENDING |
| Wave 3 | Paper Trading | PENDING |
| Wave 4 | Live Trading | PENDING |

---

# ARCHITECTURE OVERVIEW

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM BOT                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Commands   │ │   Admin     │ │  Learning   │ │ Operations │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Signal    │ │   Paper     │ │    Live     │ │  Replay    │ │
│  │  Engine    │ │   Trading   │ │   Trading   │ │  Engine    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     PROVIDER ABSTRACTION                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   Market    │ │    News     │ │     AI      │ │  Exchange  │ │
│  │   Data      │ │   Provider  │ │  Provider   │ │   Adapter  │ │
│  │  Provider   │ │             │ │             │ │            │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   SQLite    │ │   Redis     │ │    SMTP     │ │ Railway    │ │
│  │  Database   │ │   Cache     │ │   Email     │ │  Hosting   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Package Structure

```
titanbot/
├── bot/
│   ├── handlers/           # Telegram command handlers
│   ├── middleware/          # Auth, rate limiting
│   └── keyboards/           # Inline keyboards
├── core/
│   ├── state_manager.py     # ✅ Existing
│   ├── health_monitor.py     # ✅ Existing
│   ├── recovery_engine.py    # ✅ Existing
│   ├── learning_engine.py    # 🔲 Wave 2C
│   ├── news_engine.py        # 🔲 Wave 2D
│   ├── replay_engine.py      # 🔲 Wave 2E
│   ├── paper_engine.py       # 🔲 Wave 3
│   └── live_engine.py        # 🔲 Wave 4
├── engines/
│   ├── alpha_trendflow.py   # ✅ Existing
│   ├── regime_classifier.py  # ✅ Existing
│   └── confidence_engine.py  # ✅ Existing
├── providers/
│   ├── __init__.py          # Abstraction layer
│   ├── market_provider.py    # 🔲 Wave 2C
│   ├── news_provider.py      # 🔲 Wave 2D
│   ├── ai_provider.py        # 🔲 Wave 2C
│   └── exchange_adapter.py   # 🔲 Wave 4
├── models/
│   ├── signal.py
│   ├── position.py           # 🔲 Wave 3
│   ├── order.py              # 🔲 Wave 4
│   └── candle.py
├── db/
│   ├── database.py           # ✅ Existing
│   ├── migrations.py         # ✅ Existing
│   └── queries.py            # 🔲 Wave 2C
├── services/
│   ├── risk_engine.py        # 🔲 Wave 3
│   ├── position_manager.py    # 🔲 Wave 3
│   └── scheduler.py          # 🔲 Wave 3
├── config/
│   ├── settings.py           # ✅ Existing
│   └── constants.py          # ✅ Existing
├── utils/
│   ├── logging.py
│   ├── encryption.py         # 🔲 Wave 4
│   └── validation.py
└── docs/
    └── OPERATIONAL_PLAYBOOK.md
```

---

# WAVE 2C — LEARNING ENGINE

## 2C.1 Mission

Make Titan improve from historical decisions through evidence-based analysis. The Learning Engine analyzes past signals, outcomes, and performance metrics to provide actionable insights without predicting future prices.

## 2C.2 Objectives

1. Weekly performance review generation
2. Confidence score calibration analysis
3. Feature importance measurement
4. Rolling performance tracking
5. Failure classification system
6. Strategy decay detection
7. Signal explanation capability

## 2C.3 Architecture

### Module: `core/learning_engine.py`

**Responsibilities:**
- Aggregate historical signal data
- Calculate performance metrics
- Analyze confidence correlations
- Detect strategy degradation

**Dependencies:**
- `core/decision_journal.py` (signals)
- `db/database.py`
- `core/state_manager.py`

### Module: `core/analytics.py` (NEW)

**Responsibilities:**
- Statistical calculations
- Rolling window computations
- Trend analysis
- Anomaly detection

### Schema Changes

```sql
-- Add outcome tracking to signals table
ALTER TABLE signals ADD COLUMN outcome ENUM('PENDING', 'WIN', 'LOSS', 'BREAKEVEN') DEFAULT 'PENDING';
ALTER TABLE signals ADD COLUMN pnl_pct REAL DEFAULT NULL;
ALTER TABLE signals ADD COLUMN exit_price REAL DEFAULT NULL;
ALTER TABLE signals ADD COLUMN exit_time TIMESTAMP DEFAULT NULL;
ALTER TABLE signals ADD COLUMN failure_type TEXT DEFAULT NULL;
ALTER TABLE signals ADD COLUMN holding_period_hours INTEGER DEFAULT NULL;

-- Create calibration history table
CREATE TABLE IF NOT EXISTS calibration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score_range TEXT NOT NULL,  -- '35-40', '30-34', '25-29', '20-24'
    total_signals INTEGER NOT NULL,
    winning_signals INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    avg_score REAL NOT NULL,
    sample_size INTEGER NOT NULL
);

-- Create rolling performance table
CREATE TABLE IF NOT EXISTS rolling_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_size INTEGER NOT NULL,  -- 20, 50, 100
    trade_count INTEGER NOT NULL,
    win_count INTEGER NOT NULL,
    loss_count INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    expectancy REAL NOT NULL,
    avg_confidence REAL NOT NULL,
    consecutive_wins INTEGER DEFAULT 0,
    consecutive_losses INTEGER DEFAULT 0,
    max_drawdown REAL DEFAULT 0
);

-- Create feature importance table
CREATE TABLE IF NOT EXISTS feature_importance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feature_name TEXT NOT NULL,
    importance_score REAL NOT NULL,
    sample_size INTEGER NOT NULL,
    confidence_interval REAL DEFAULT 0.95
);

-- Create decay detection table
CREATE TABLE IF NOT EXISTS decay_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_start DATE NOT NULL,
    window_end DATE NOT NULL,
    previous_win_rate REAL NOT NULL,
    current_win_rate REAL NOT NULL,
    decay_pct REAL NOT NULL,
    significance REAL NOT NULL,
    alert_triggered BOOLEAN DEFAULT FALSE
);
```

### Indexes

```sql
CREATE INDEX idx_signals_outcome ON signals(outcome);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_setup_type ON signals(setup_type);
CREATE INDEX idx_signals_regime ON signals(regime);
CREATE INDEX idx_calibration_range ON calibration_history(score_range);
CREATE INDEX idx_rolling_window ON rolling_performance(window_size);
```

### API: Learning Engine

```python
class LearningEngine:
    """Titan Learning Engine API"""
    
    async def get_weekly_review(
        weeks_back: int = 1
    ) -> WeeklyReport:
        """
        Generate weekly performance review.
        
        Returns:
            WeeklyReport with full statistics
        """
        
    async def analyze_confidence_calibration(
        min_samples: int = 20
    ) -> CalibrationAnalysis:
        """
        Analyze if confidence correlates with outcomes.
        
        Returns:
            CalibrationAnalysis with ranges and correlations
        """
        
    async def analyze_feature_importance(
        lookback_signals: int = 200
    ) -> FeatureImportanceReport:
        """
        Measure contribution of each scoring component.
        
        Returns:
            FeatureImportanceReport with percentages
        """
        
    async def get_rolling_performance(
        windows: list[int] = [20, 50, 100]
    ) -> RollingPerformanceReport:
        """
        Get rolling window statistics.
        
        Returns:
            RollingPerformanceReport for each window
        """
        
    async def classify_failure(
        signal_id: int,
        failure_type: FailureType
    ) -> bool:
        """
        Classify a losing trade's failure reason.
        
        Args:
            signal_id: Signal to classify
            failure_type: One of 8 failure types
            
        Returns:
            True if classified successfully
        """
        
    async def detect_strategy_decay(
        window_days: int = 30,
        significance_threshold: float = 0.05
    ) -> list[DecaySignal]:
        """
        Detect if strategy performance is degrading.
        
        Returns:
            List of decay signals above threshold
        """
        
    async def get_signal_explanation(
        signal_id: int
    ) -> SignalExplanation:
        """
        Get full explanation of a signal decision.
        
        Returns:
            SignalExplanation with all factors
        """
```

### Commands (Wave 2C)

| Command | Permissions | Description |
|---------|-------------|-------------|
| `/weekly_review` | User | Weekly performance report |
| `/calibration` | User | Confidence calibration analysis |
| `/feature_importance` | User | Factor importance analysis |
| `/rolling_stats` | User | Rolling window statistics |
| `/failures` | User | Failure type analysis |
| `/decay` | Admin | Strategy decay detection |
| `/explain <id>` | User | Signal decision explanation |

### Health & Recovery

| Component | Failure Mode | Detection | Recovery | Max Retries |
|-----------|--------------|-----------|----------|-------------|
| Learning Engine | Calculation exception | Try/except | Return cached or empty | N/A |
| Database query | Query timeout | 30s timeout | Return cached data | 3 |
| Calibration | Insufficient data | < 20 samples | Return partial with warning | N/A |

### Testing

```python
# tests/test_learning_engine.py

class TestWeeklyReview:
    def test_empty_week_returns_zeros(self):
        """No signals returns empty report."""
        
    def test_calculates_win_rate_correctly(self):
        """Win rate = wins / total."""
        
    def test_grouped_by_regime(self):
        """Regimes grouped separately."""
        
    def test_streak_calculation(self):
        """Win/loss streaks calculated correctly."""

class TestCalibration:
    def test_score_ranges_defined(self):
        """35-40, 30-34, 25-29, 20-24."""
        
    def test_correlation_calculation(self):
        """Confidence vs outcome correlation."""
        
    def test_minimum_sample_warning(self):
        """< 20 samples returns warning."""

class TestFailureClassification:
    def test_all_8_types_available(self):
        """REGIME_MISMATCH through UNKNOWN."""
        
    def test_invalid_type_rejected(self):
        """Unknown type returns False."""
        
    def test_stored_in_signal(self):
        """Failure type persisted."""
```

### Definition of Done (Wave 2C)

- [ ] `/weekly_review` returns complete statistics
- [ ] `/calibration` shows score-to-outcome correlation
- [ ] `/feature_importance` ranks scoring components
- [ ] Rolling stats for 20/50/100 windows working
- [ ] All 8 failure types classifiable
- [ ] `/explain <id>` shows full signal reasoning
- [ ] Decay detection alerts when WR drops >10%
- [ ] All tests passing
- [ ] Documentation updated
- [ ] **STOP GATE:** Manual review by architect

---

# WAVE 2D — NEWS INTELLIGENCE

## 2D.1 Mission

Integrate news intelligence into Titan's decision process. News events cause volatility and regime changes. Titan must detect, classify, and adjust for news events without depending on expensive third-party services.

## 2D.2 Objectives

1. Free news API integration (CryptoPanic, NewsAPI)
2. News event classification
3. Risk adjustment based on news
4. News decay modeling
5. Event cluster detection
6. News-based regime validation
7. News command interface

## 2D.3 Architecture

### Provider: `providers/news_provider.py`

**Interface:**
```python
from abc import ABC, abstractmethod

class NewsProvider(ABC):
    """Abstract news provider interface."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        
    @abstractmethod
    async def fetch_news(
        self,
        symbols: list[str],
        hours_back: int = 24
    ) -> list[NewsItem]:
        """
        Fetch news items for symbols.
        
        Args:
            symbols: Trading pairs ['BTCUSD', 'ETHUSD']
            hours_back: Lookback period
            
        Returns:
            List of NewsItem objects
        """
        
    @abstractmethod
    async def search_news(
        self,
        query: str,
        limit: int = 50
    ) -> list[NewsItem]:
        """Search news by query."""
```

### Implementation: `providers/cryptopanic.py`

**Authentication:** Free API key from cryptopanic.com

**Rate Limits:**
- Free tier: 100 requests/hour
- Implementation: Cache results 15 minutes

**Timeout Strategy:**
- Connect: 5 seconds
- Read: 10 seconds

**Retry Strategy:**
- 3 retries with exponential backoff (1s, 2s, 4s)

**Fallback:**
- If CryptoPanic fails, return empty list
- Log warning, continue without news adjustment

### Module: `core/news_engine.py`

**Responsibilities:**
- Aggregate news from providers
- Classify news sentiment
- Calculate news impact score
- Detect event clusters
- Apply news risk adjustments

### Schema Changes

```sql
-- Create news items table
CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    provider TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    source TEXT,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment_score REAL DEFAULT 0,  -- -1.0 to 1.0
    sentiment_label TEXT,  -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    impact_score REAL DEFAULT 0,  -- 0 to 10
    relevance_score REAL DEFAULT 0,  -- 0 to 10
    symbols TEXT,  -- JSON array
    categories TEXT,  -- JSON array
    processed BOOLEAN DEFAULT FALSE
);

-- Create news-symbol mapping
CREATE TABLE IF NOT EXISTS news_symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER REFERENCES news_items(id),
    symbol TEXT NOT NULL,
    relevance REAL DEFAULT 0
);

-- Create news events table
CREATE TABLE IF NOT EXISTS news_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'HALVING', 'ETF', 'REGULATION', 'HACK', 'PARTNERSHIP'
    severity INTEGER NOT NULL,  -- 1-5
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    affected_symbols TEXT,  -- JSON array
    description TEXT,
    volatility_impact REAL,  -- Expected % move
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create news risk adjustments table
CREATE TABLE IF NOT EXISTS news_risk_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    adjustment_factor REAL NOT NULL,  -- 0.0 to 1.0
    reason TEXT,
    news_event_id INTEGER REFERENCES news_events(id),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Create news command log
CREATE TABLE IF NOT EXISTS news_command_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    symbols_requested TEXT,
    results_count INTEGER,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER
);
```

### Indexes

```sql
CREATE INDEX idx_news_symbols ON news_symbols(symbol);
CREATE INDEX idx_news_published ON news_items(published_at);
CREATE INDEX idx_news_sentiment ON news_items(sentiment_score);
CREATE INDEX idx_events_time ON news_events(start_time);
CREATE INDEX idx_events_symbols ON news_events(affected_symbols);
CREATE INDEX idx_risk_active ON news_risk_adjustments(active, expires_at);
```

### News Event Types

| Event Type | Severity | Volatility Impact | Example |
|-------------|----------|-------------------|---------|
| `MAJOR_NEWS` | 5 | ±15% | ETF approval |
| `EXCHANGE_LISTING` | 4 | ±8% | Coinbase listing |
| `PARTNERSHIP` | 3 | ±5% | Major partnership |
| `REGULATORY` | 4 | ±10% | SEC statement |
| `TECH_UPGRADE` | 2 | ±3% | Network upgrade |
| `MARKET_NEWS` | 3 | ±5% | Macro news |
| `SOCIAL_FOMO` | 2 | ±4% | Viral tweet |
| `FLUFF` | 1 | ±1% | Non-substantive |

### Commands (Wave 2D)

| Command | Permissions | Description |
|---------|-------------|-------------|
| `/news <symbol>` | User | Latest news for symbol |
| `/news_risk <symbol>` | User | Current news risk score |
| `/news_history <symbol>` | User | News history for symbol |
| `/news_sources` | Admin | List configured providers |
| `/news_add <source>` | Admin | Add news source |

### Health & Recovery

| Component | Failure Mode | Detection | Recovery | Max Retries |
|-----------|--------------|-----------|----------|-------------|
| News API | Rate limit hit | 429 response | Wait 1 hour | N/A |
| News API | Timeout | 30s elapsed | Return cached | 3 |
| News API | Invalid response | JSON parse fail | Return empty | N/A |
| News API | No API key | Missing key | Use free tier | N/A |
| Sentiment | Analysis error | Exception | Default NEUTRAL | N/A |

### STOP GATE (Wave 2D)

**⚠️ STOP HERE: WAIT FOR CREDENTIALS**

```
NEWS_API_KEY: _______________  (Optional - CryptoPanic free tier works without)
```

- [ ] News fetching working
- [ ] Sentiment analysis implemented
- [ ] Risk adjustment applied to signals
- [ ] `/news` command functional
- [ ] News stored in database
- [ ] Commands documented
- [ ] **STOP GATE:** Manual review

---

# WAVE 2E — HISTORICAL REPLAY ENGINE

## 2E.1 Mission

Enable historical validation of trading strategies. Titan must replay historical market data, execute signals as if trading live, and measure performance without risking capital.

## 2E.2 Objectives

1. Historical data provider abstraction
2. Replay framework with pause/resume
3. Historical signal execution
4. Performance metrics generation
5. Replay command interface
6. Replay report storage

## 2E.3 Architecture

### Provider: `providers/historical_provider.py`

```python
class HistoricalDataProvider(ABC):
    """Abstract historical data provider."""
    
    @abstractmethod
    async def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> list[Candle]:
        """Fetch historical candles."""
        
    @abstractmethod
    async def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> list[Candle]:
        """Fetch limited historical bars."""
```

### Implementation: `providers/ccxt_historical.py`

- Uses CCXT `fetch_ohlcv` with `since` parameter
- Falls back to `fetch_binance_ohlcv` if exchange unavailable
- Rate limiting: 1200 requests/minute

### Module: `core/replay_engine.py`

**Responsibilities:**
- Control replay state (play, pause, stop, speed)
- Execute signals on historical data
- Track virtual positions
- Calculate replay performance
- Generate replay reports

### Schema Changes

```sql
-- Create replay sessions table
CREATE TABLE IF NOT EXISTS replay_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'RUNNING', 'PAUSED', 'COMPLETED', 'ABORTED'
    symbol TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    timeframe TEXT DEFAULT '1h',
    initial_balance REAL DEFAULT 10000,
    final_balance REAL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    max_drawdown REAL DEFAULT 0,
    sharpe_ratio REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create replay signals table
CREATE TABLE IF NOT EXISTS replay_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    replay_session_id INTEGER REFERENCES replay_sessions(id),
    signal_id INTEGER REFERENCES signals(id),  -- Original signal
    executed_at TIMESTAMP NOT NULL,
    action TEXT NOT NULL,  -- 'LONG', 'SHORT', 'WAIT'
    entry_price REAL NOT NULL,
    exit_price REAL,
    pnl_pct REAL,
    outcome TEXT,  -- 'WIN', 'LOSS'
    setup_type TEXT,
    regime TEXT,
    confidence INTEGER,
    replay_date DATE NOT NULL
);

-- Create replay reports table
CREATE TABLE IF NOT EXISTS replay_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    replay_session_id INTEGER REFERENCES replay_sessions(id),
    report_type TEXT NOT NULL,  -- 'FULL', 'PARTIAL'
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metrics_json TEXT,  -- Full metrics as JSON
    recommendations TEXT
);
```

### Commands (Wave 2E)

| Command | Permissions | Description |
|---------|-------------|-------------|
| `/replay <symbol>` | Admin | Start replay session |
| `/replay_status` | Admin | Current replay status |
| `/replay_stop` | Admin | Stop current replay |
| `/replay_pause` | Admin | Pause replay |
| `/replay_resume` | Admin | Resume replay |
| `/replay_report` | Admin | Get replay report |
| `/replay_history` | Admin | List past replays |

### Health & Recovery

| Component | Failure Mode | Detection | Recovery | Max Retries |
|-----------|--------------|-----------|----------|-------------|
| Historical API | No data for range | Empty return | Log error | 3 |
| Historical API | Gap in data | Missing candles | Mark gap, continue | N/A |
| Replay | Memory overflow | > 10K candles | Batch processing | N/A |
| Replay | Interrupted | SIGTERM | Save state, resume | N/A |

### STOP GATE (Wave 2E)

- [ ] Replay executes on historical data
- [ ] Virtual trades recorded
- [ ] Performance metrics calculated
- [ ] Replay reports generated
- [ ] Commands functional
- [ ] **STOP GATE:** Manual review

---

# WAVE 3 — PAPER TRADING

## 3.1 Mission

Implement full paper trading capability. Titan executes trades in a simulated environment using real market data. This validates the complete trading loop before risking capital.

## 3.2 Objectives

1. Paper execution engine
2. Virtual portfolio management
3. Risk engine implementation
4. Position management
5. P&L calculation
6. Trade lifecycle management
7. Paper trading scheduler
8. Daily paper reports

## 3.3 Architecture

### Module: `core/paper_engine.py`

**Responsibilities:**
- Execute virtual trades
- Manage paper portfolio state
- Track open positions
- Calculate unrealized P&L
- Close positions on signals
- Apply risk rules

### Module: `core/risk_engine.py`

**Responsibilities:**
- Position sizing
- Stop loss calculation
- Take profit calculation
- Drawdown monitoring
- Exposure limits
- Correlation checks

### Module: `core/position_manager.py`

**Responsibilities:**
- Position lifecycle
- Entry/exit logic
- Order management
- Position tracking

### Schema Changes

```sql
-- Create paper positions table
CREATE TABLE IF NOT EXISTS paper_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,  -- 'LONG', 'SHORT'
    entry_price REAL NOT NULL,
    quantity REAL NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    current_price REAL,
    unrealized_pnl REAL DEFAULT 0,
    unrealized_pnl_pct REAL DEFAULT 0,
    status TEXT DEFAULT 'OPEN',  -- 'OPEN', 'CLOSED', 'STOPPED', 'LIMITED'
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    close_price REAL,
    close_reason TEXT,  -- 'SIGNAL', 'STOP_LOSS', 'TAKE_PROFIT', 'MANUAL'
    realized_pnl REAL,
    setup_type TEXT,
    signal_id INTEGER REFERENCES signals(id),
    replay_session_id INTEGER
);

-- Create paper orders table
CREATE TABLE IF NOT EXISTS paper_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER REFERENCES paper_positions(id),
    order_type TEXT NOT NULL,  -- 'MARKET', 'LIMIT', 'STOP'
    side TEXT NOT NULL,
    price REAL,
    quantity REAL,
    filled BOOLEAN DEFAULT FALSE,
    filled_at TIMESTAMP,
    filled_price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create paper portfolio table
CREATE TABLE IF NOT EXISTS paper_portfolio (
    id INTEGER PRIMARY KEY,
    balance REAL NOT NULL DEFAULT 10000,
    equity REAL NOT NULL DEFAULT 10000,
    reserved REAL DEFAULT 0,
    drawdown REAL DEFAULT 0,
    peak_equity REAL DEFAULT 10000,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create paper trades history
CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER REFERENCES paper_positions(id),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    quantity REAL NOT NULL,
    pnl REAL NOT NULL,
    pnl_pct REAL NOT NULL,
    commission REAL DEFAULT 0,
    held_hours REAL,
    closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    setup_type TEXT,
    regime TEXT,
    confidence INTEGER
);

-- Create daily paper reports
CREATE TABLE IF NOT EXISTS paper_daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    starting_balance REAL NOT NULL,
    ending_balance REAL NOT NULL,
    daily_pnl REAL NOT NULL,
    daily_pnl_pct REAL NOT NULL,
    trades_count INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    open_positions INTEGER DEFAULT 0,
    max_drawdown REAL DEFAULT 0,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create paper settings table
CREATE TABLE IF NOT EXISTS paper_settings (
    id INTEGER PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    initial_balance REAL DEFAULT 10000,
    max_position_pct REAL DEFAULT 10,
    max_total_exposure_pct REAL DEFAULT 50,
    stop_loss_pct REAL DEFAULT 2.0,
    take_profit_pct REAL DEFAULT 6.0,
    max_daily_trades INTEGER DEFAULT 5,
    max_consecutive_losses INTEGER DEFAULT 3,
    drawdown_limit_pct REAL DEFAULT 10,
    auto_close_eod BOOLEAN DEFAULT TRUE,
    trading_hours_start TEXT DEFAULT '00:00',
    trading_hours_end TEXT DEFAULT '23:59',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Risk Engine Rules

| Rule | Default | Description |
|------|---------|-------------|
| `max_position_pct` | 10% | Max position as % of equity |
| `max_total_exposure` | 50% | Max all positions |
| `stop_loss_pct` | 2.0% | Default stop loss |
| `take_profit_pct` | 6.0% | Default take profit |
| `max_daily_trades` | 5 | Max trades per day |
| `max_consecutive_losses` | 3 | Pause after 3 losses |
| `drawdown_limit` | 10% | Stop trading at drawdown |

### Commands (Wave 3)

| Command | Permissions | Description |
|---------|-------------|-------------|
| `/paper_start` | Admin | Start paper trading |
| `/paper_stop` | Admin | Stop paper trading |
| `/paper_status` | Admin | Paper trading status |
| `/paper_positions` | User | Open positions |
| `/paper_trades` | User | Trade history |
| `/paper_pnl` | User | P&L summary |
| `/paper_report` | Admin | Daily report |
| `/paper_reset` | Admin | Reset portfolio |
| `/paper_settings` | Admin | View/manage settings |

### Health & Recovery

| Component | Failure Mode | Detection | Recovery | Max Retries |
|-----------|--------------|-----------|----------|-------------|
| Paper Engine | Position calculation error | Exception | Log, skip trade | N/A |
| Risk Engine | Limit exceeded | Check fails | Reject trade | N/A |
| Portfolio | Balance mismatch | Audit | Freeze, alert | N/A |
| Position | Orphaned position | No close time | Auto-close EOD | N/A |
| Scheduler | Missed candle | Timestamp gap | Catch up | N/A |

### STOP GATE (Wave 3)

**⚠️ STOP HERE: REVIEW PAPER TRADING LOGIC**

- [ ] Paper trades execute
- [ ] Positions tracked
- [ ] P&L calculated
- [ ] Risk rules enforced
- [ ] Daily reports generated
- [ ] Commands functional
- [ ] **STOP GATE:** 2 weeks paper trading validated

---

# WAVE 4 — LIVE TRADING

## 4.1 Mission

Enable live trading with exchange API integration. Titan executes real trades, manages real positions, and handles production-grade requirements including security, monitoring, and emergency controls.

**CRITICAL: This wave introduces financial risk.**

## 4.2 Objectives

1. Exchange API integration
2. API key encryption
3. Atomic order execution
4. Position reconciliation
5. Emergency controls
6. Production monitoring
7. Rollback strategy

## 4.3 Architecture

### Module: `core/live_engine.py`

**Responsibilities:**
- Exchange connection management
- Order placement
- Order tracking
- Position reconciliation
- Balance monitoring

### Module: `core/exchange_adapter.py`

```python
from abc import ABC, abstractmethod

class ExchangeAdapter(ABC):
    """Abstract exchange adapter interface."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name."""
        
    @property
    @abstractmethod
    def rate_limit(self) -> int:
        """Requests per minute."""
    
    @abstractmethod
    async def fetch_balance(self) -> Balance:
        """Get account balance."""
        
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None
    ) -> OrderResult:
        """Place an order."""
        
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        
    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get open positions."""
        
    @abstractmethod
    async def get_orders(self, symbol: str = None) -> list[Order]:
        """Get open orders."""
```

### Implementation: `providers/binance_adapter.py`

**Authentication:** API Key + Secret (encrypted at rest)

**Rate Limits:**
- Spot: 1200 requests/minute
- Orders: 10 orders/second

**Timeout Strategy:**
- Connect: 5 seconds
- Read: 10 seconds

**Retry Strategy:**
- Retry on 5xx, 429
- Exponential backoff

**Emergency Stop:**
- All positions closed
- All orders cancelled

### Module: `utils/encryption.py`

```python
from cryptography.fernet import Fernet
import base64
import hashlib

class KeyEncryption:
    """Secure key storage using Fernet."""
    
    def __init__(self, master_key: str):
        # Derive key from master
        key = hashlib.sha256(master_key.encode()).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt API credentials."""
        return self._fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt API credentials."""
        return self._fernet.decrypt(ciphertext.encode()).decode()
```

### Schema Changes

```sql
-- Create live positions table
CREATE TABLE IF NOT EXISTS live_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL NOT NULL,
    quantity REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL DEFAULT 0,
    stop_loss REAL,
    take_profit REAL,
    status TEXT DEFAULT 'OPEN',
    exchange_order_id TEXT,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    close_price REAL,
    close_reason TEXT,
    realized_pnl REAL
);

-- Create live orders table
CREATE TABLE IF NOT EXISTS live_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    order_id TEXT UNIQUE,
    client_order_id TEXT,
    order_type TEXT NOT NULL,
    side TEXT NOT NULL,
    price REAL,
    quantity REAL,
    filled_quantity REAL DEFAULT 0,
    avg_fill_price REAL,
    status TEXT NOT NULL,  -- 'NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED', 'REJECTED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create exchange credentials table (encrypted)
CREATE TABLE IF NOT EXISTS exchange_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT UNIQUE NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT NOT NULL,
    passphrase_encrypted TEXT,  -- For exchanges that require it
    testnet BOOLEAN DEFAULT FALSE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create live portfolio snapshot
CREATE TABLE IF NOT EXISTS live_portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_equity REAL NOT NULL,
    available_balance REAL NOT NULL,
    position_count INTEGER DEFAULT 0,
    unrealized_pnl REAL DEFAULT 0,
    daily_pnl REAL DEFAULT 0
);

-- Create emergency log
CREATE TABLE IF NOT EXISTS emergency_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emergency_type TEXT NOT NULL,
    triggered_by TEXT,
    positions_closed INTEGER DEFAULT 0,
    orders_cancelled INTEGER DEFAULT 0,
    balance_at_trigger REAL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Commands (Wave 4)

| Command | Permissions | Description |
|---------|-------------|-------------|
| `/connect <exchange>` | Admin | Connect exchange |
| `/disconnect` | Admin | Disconnect exchange |
| `/account` | Admin | Account summary |
| `/balance` | Admin | Balance details |
| `/positions` | User | Open positions |
| `/orders` | User | Open orders |
| `/portfolio` | User | Portfolio summary |
| `/close_position <id>` | Admin | Close specific position |
| `/close_all` | Admin | Emergency close all |
| `/emergency_stop` | Admin | Full emergency stop |

### Health & Recovery

| Component | Failure Mode | Detection | Recovery | Max Retries |
|-----------|--------------|-----------|----------|-------------|
| Exchange | Connection lost | WebSocket disconnect | Reconnect | ∞ |
| Exchange | Rate limited | 429 response | Backoff | N/A |
| Exchange | Insufficient balance | API error | Reject order | N/A |
| Order | Not filled | Timeout | Cancel, retry | 3 |
| Order | Partial fill | Fill update | Track remainder | N/A |
| Position | Mismatch | Reconciliation | Sync from exchange | N/A |
| Credentials | Decryption fail | Exception | Alert admin | N/A |

### STOP GATE (Wave 4)

**⚠️ STOP HERE: WAIT FOR CREDENTIALS**

```
EXCHANGE_API_KEY: _______________
EXCHANGE_API_SECRET: _______________
MASTER_ENCRYPTION_KEY: _______________
```

- [ ] Exchange connected
- [ ] Test order placed (small qty)
- [ ] Positions tracked
- [ ] Orders tracked
- [ ] Emergency stop tested
- [ ] Reconciliation working
- [ ] **STOP GATE:** Manual approval required
- [ ] **STOP GATE:** Risk review required

---

# HEALTH MANUAL

## System Health States

### Definition

| State | Score | Description | Action |
|-------|-------|-------------|--------|
| HEALTHY | 80-100% | All systems nominal | Continue |
| WARNING | 60-79% | Minor issues detected | Investigate |
| CRITICAL | 40-59% | Major issues, trading paused | Recover |
| EMERGENCY | 0-39% | System failure, all halted | Manual intervention |

## Subsystem Runbooks

### Exchange Connection

**Normal:** Connected, receiving data, latency < 500ms

**Warning:**
- Latency > 1s
- Intermittent disconnects
- Rate limit approaching

**Critical:**
- No data for > 5 minutes
- Consistent 5xx errors
- Authentication failures

**Recovery:**
1. Retry connection with backoff
2. Switch to backup provider
3. Enter Safe Mode
4. Alert admin

---

### Database

**Normal:** Queries < 100ms, no locks

**Warning:**
- Query time > 1s
- Increasing lock waits
- Disk usage > 80%

**Critical:**
- Lock timeout
- Disk full
- Corruption detected

**Recovery:**
1. Retry with longer timeout
2. Free disk space
3. Run integrity check
4. Restore from backup if corrupted

---

### Telegram Bot

**Normal:** Commands responsive, < 2s response

**Warning:**
- Response time > 5s
- Rate limit approaching

**Critical:**
- Commands failing
- Complete outage

**Recovery:**
1. Check Telegram API status
2. Retry failed messages
3. Queue notifications
4. Alert admin if persistent

---

### Risk Engine

**Normal:** Rules applied, limits enforced

**Warning:**
- Position near limit
- Drawdown approaching threshold

**Critical:**
- Risk calculation failure
- Limit enforcement failure

**Recovery:**
1. Reject all new trades
2. Keep existing positions
3. Alert admin immediately
4. Manual review required

---

### Scheduler

**Normal:** Tasks running on schedule

**Warning:**
- Task delayed < 5 minutes
- Task skipped once

**Critical:**
- Tasks not running
- Multiple skipped tasks

**Recovery:**
1. Restart scheduler
2. Catch up on missed tasks
3. Log gaps
4. Alert if persistent

---

## Emergency Procedures

### Exchange Outage > 5 Minutes

```
IF exchange unreachable for 5 minutes:
    THEN:
        1. Enter SAFE_MODE
        2. Stop new trade signals
        3. Keep existing positions
        4. Alert admin
        5. Log incident
        
    IF exchange returns:
        THEN:
            1. Verify data integrity
            2. Resume normal operation
            3. Log recovery
```

### Database Corruption

```
IF corruption detected:
    THEN:
        1. Enter ERROR state
        2. Stop all trading immediately
        3. Attempt repair
        4. If repair fails:
            a. Restore from backup
            b. Notify admin
            c. Require manual approval
```

### Risk Limit Breach

```
IF risk limit exceeded unexpectedly:
    THEN:
        1. Reject trade immediately
        2. Log full context
        3. Enter SAFE_MODE
        4. Alert admin
        5. Require manual review
```

---

# COMMAND INTERFACE

## Complete Command Reference

### General Commands

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/start` | 1 | User | None | `/start` |
| `/help` | 1 | User | None | `/help` |
| `/status` | 1 | User | None | `/status` |

### Market Intelligence

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/signal <pair>` | 2A | User | Pair | `/signal BTCUSDT` |
| `/regime <pair>` | 2A | User | Pair | `/regime ETHUSD` |
| `/score <pair>` | 2A | User | Pair | `/score SOLUSDT` |

### Learning & Analytics

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/journal` | 2B | User | None | `/journal` |
| `/expectancy` | 2B | User | None | `/expectancy` |
| `/weekly_review` | 2C | User | [weeks] | `/weekly_review 2` |
| `/calibration` | 2C | User | None | `/calibration` |
| `/feature_importance` | 2C | User | None | `/feature_importance` |
| `/rolling_stats` | 2C | User | [windows] | `/rolling_stats 50` |
| `/failures` | 2C | User | None | `/failures` |
| `/explain <id>` | 2C | User | Signal ID | `/explain 42` |
| `/decay` | 2C | Admin | None | `/decay` |

### News

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/news <symbol>` | 2D | User | Symbol | `/news BTC` |
| `/news_risk <symbol>` | 2D | User | Symbol | `/news_risk ETH` |
| `/news_history` | 2D | User | Symbol | `/news_history BTC` |

### Historical Replay

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/replay <symbol>` | 2E | Admin | Symbol | `/replay BTCUSD` |
| `/replay_status` | 2E | Admin | None | `/replay_status` |
| `/replay_stop` | 2E | Admin | None | `/replay_stop` |
| `/replay_report` | 2E | Admin | [ID] | `/replay_report 3` |

### Paper Trading

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/paper_start` | 3 | Admin | None | `/paper_start` |
| `/paper_stop` | 3 | Admin | None | `/paper_stop` |
| `/paper_status` | 3 | User | None | `/paper_status` |
| `/paper_positions` | 3 | User | None | `/paper_positions` |
| `/paper_trades` | 3 | User | [limit] | `/paper_trades 20` |
| `/paper_pnl` | 3 | User | None | `/paper_pnl` |
| `/paper_reset` | 3 | Admin | None | `/paper_reset` |

### Live Trading

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/connect <exchange>` | 4 | Admin | Exchange | `/connect binance` |
| `/disconnect` | 4 | Admin | None | `/disconnect` |
| `/account` | 4 | Admin | None | `/account` |
| `/balance` | 4 | Admin | None | `/balance` |
| `/positions` | 4 | User | None | `/positions` |
| `/orders` | 4 | User | [symbol] | `/orders BTC` |
| `/close_position <id>` | 4 | Admin | Position ID | `/close_position 42` |
| `/close_all` | 4 | Admin | None | `/close_all` |
| `/emergency_stop` | 4 | Admin | None | `/emergency_stop` |

### Operations

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/health` | 2D | User | None | `/health` |
| `/health_report` | 2D | User | None | `/health_report` |
| `/system_state` | 2D | User | None | `/system_state` |
| `/recovery` | 2D | User | None | `/recovery` |
| `/diagnostics` | 2D | User | None | `/diagnostics` |

### Administration

| Command | Wave | Permissions | Args | Example |
|---------|------|-------------|------|---------|
| `/authorize <PIN>` | 1 | Admin | PIN | `/authorize 123456` |
| `/dashboard` | 1 | Admin | None | `/dashboard` |
| `/users` | 1 | Admin | None | `/users` |
| `/pending` | 2B | Admin | None | `/pending` |
| `/approve <id>` | 2B | Admin | User ID | `/approve 123456` |
| `/reject <id>` | 2B | Admin | User ID | `/reject 123456` |
| `/suspend <id>` | 2B | Admin | User ID | `/suspend 123456` |
| `/resume <id>` | 2B | Admin | User ID | `/resume 123456` |
| `/classify <id> <type>` | 2C | Admin | ID, Type | `/classify 42 STOP_HUNT` |
| `/risk` | 2B | Admin | None | `/risk` |
| `/enable_trading` | 2B | Admin | None | `/enable_trading` |
| `/disable_trading` | 2B | Admin | None | `/disable_trading` |
| `/logs` | 1 | Admin | [count] | `/logs 50` |
| `/version` | 1 | Admin | None | `/version` |

---

# IMPLEMENTATION CHECKLISTS

## Wave 2C Checklist

### Engineering
- [ ] `core/learning_engine.py` created
- [ ] `core/analytics.py` created
- [ ] Database migrations for calibration, rolling, decay
- [ ] Weekly report calculation
- [ ] Confidence calibration analysis
- [ ] Feature importance calculation
- [ ] Rolling performance tracking
- [ ] Failure classification (8 types)
- [ ] Signal explanation generation
- [ ] Strategy decay detection

### Testing
- [ ] Unit tests: Weekly report calculation
- [ ] Unit tests: Calibration ranges
- [ ] Unit tests: Feature importance
- [ ] Unit tests: Streak calculation
- [ ] Integration: Database queries
- [ ] Edge cases: Empty data, insufficient samples

### Documentation
- [ ] Update README with new commands
- [ ] Add learning engine docs
- [ ] Document failure types
- [ ] Add troubleshooting guide

### Deployment
- [ ] Migration tested locally
- [ ] Migration tested on Railway
- [ ] Bot commands registered
- [ ] Health check updated

### **STOP GATE: Wave 2C**
- [ ] All tests passing
- [ ] Commands functional on Telegram
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] **MANUAL REVIEW APPROVED**

---

## Wave 2D Checklist

### Engineering
- [ ] `providers/news_provider.py` interface
- [ ] `providers/cryptopanic.py` implementation
- [ ] `core/news_engine.py` created
- [ ] News database tables
- [ ] Sentiment analysis
- [ ] Risk adjustment integration
- [ ] News commands implemented

### Testing
- [ ] Unit tests: News fetching
- [ ] Unit tests: Sentiment scoring
- [ ] Integration: Provider abstraction
- [ ] Failure: API unavailable
- [ ] Failure: Rate limited

### **STOP GATE: Wave 2D**
- [ ] News commands functional
- [ ] Risk adjustments applied
- [ ] **MANUAL REVIEW APPROVED**

---

## Wave 2E Checklist

### Engineering
- [ ] `providers/historical_provider.py` interface
- [ ] `providers/ccxt_historical.py` implementation
- [ ] `core/replay_engine.py` created
- [ ] Replay database tables
- [ ] Play/pause/stop functionality
- [ ] Performance calculation
- [ ] Replay commands

### Testing
- [ ] Unit tests: Replay logic
- [ ] Integration: Historical data
- [ ] Replay: 1 week backtest
- [ ] Replay: 1 month backtest

### **STOP GATE: Wave 2E**
- [ ] Replay working correctly
- [ ] Reports generated
- [ ] **MANUAL REVIEW APPROVED**

---

## Wave 3 Checklist

### Engineering
- [ ] `core/paper_engine.py` created
- [ ] `core/risk_engine.py` created
- [ ] `core/position_manager.py` created
- [ ] Paper database tables
- [ ] Position lifecycle
- [ ] P&L calculation
- [ ] Risk rules enforced
- [ ] Daily reports
- [ ] Paper commands

### Security
- [ ] No real API keys in paper mode
- [ ] Position limits enforced
- [ ] Drawdown limits enforced

### Testing
- [ ] Unit tests: Risk calculations
- [ ] Unit tests: P&L calculation
- [ ] Paper: 1 week trading
- [ ] Paper: 2 weeks trading
- [ ] Failure: Risk limit
- [ ] Recovery: Restart during trade

### **STOP GATE: Wave 3**
- [ ] 2 weeks paper trading validated
- [ ] P&L matches expected
- [ ] Risk rules tested
- [ ] **MANUAL REVIEW APPROVED**

---

## Wave 4 Checklist

### Engineering
- [ ] `providers/exchange_adapter.py` interface
- [ ] `providers/binance_adapter.py` implementation
- [ ] `core/live_engine.py` created
- [ ] `utils/encryption.py` created
- [ ] Live database tables
- [ ] API key encryption
- [ ] Order placement
- [ ] Position tracking
- [ ] Emergency controls
- [ ] Live commands

### Security
- [ ] API keys encrypted at rest
- [ ] No keys in logs
- [ ] No keys in errors
- [ ] Master key required at startup

### Testing
- [ ] Testnet trading
- [ ] Small quantity orders
- [ ] Order fills
- [ ] Position tracking
- [ ] Emergency stop
- [ ] Reconciliation

### **STOP GATES: Wave 4**
- [ ] Testnet validated
- [ ] Risk review completed
- [ ] Security audit passed
- [ ] Emergency procedures tested
- [ ] Rollback plan documented
- [ ] **MANUAL APPROVAL: TWO PEOPLE REQUIRED**
- [ ] **MANUAL APPROVAL: RISK DISCLAIMER SIGNED**

---

# CREDENTIAL PAUSE POINTS

## Wave 2C
None required.

## Wave 2D
```
⚠️ STOP HERE (Optional)
NEWS_API_KEY: _______________
```
CryptoPanic free tier works without key. Premium features require key.

## Wave 2E
None required.

## Wave 3
None required. Paper trading uses no external credentials.

## Wave 4
```
⚠️ STOP HERE - WAIT FOR CREDENTIALS

EXCHANGE_API_KEY: _______________
EXCHANGE_API_SECRET: _______________
EXCHANGE_PASSPHRASE: _______________ (if required)
MASTER_ENCRYPTION_KEY: _______________

⚠️ CRITICAL: Generate encryption key offline.
⚠️ CRITICAL: Never commit credentials.
⚠️ CRITICAL: Two-person approval for production keys.
```

---

# FINAL SIGN-OFF

This specification represents the complete engineering roadmap for Titan Trading Intelligence Platform from Wave 2C through Wave 4.

**Estimated Implementation:** 8-12 weeks  
**Team Size:** 1-2 engineers  
**Risk Level:** Increases with each wave

---

**Document Status:** READY FOR IMPLEMENTATION

**Prepared By:** TITAN Infrastructure Agent  
**Date:** June 2026  
**Version:** 1.0

---

*Build Titan once. Build it correctly.*
