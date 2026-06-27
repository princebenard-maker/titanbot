# 🤖 TITAN
### AI-Powered Crypto Trading Intelligence

*Survival First. Evidence-Driven. Always Learning.*

---

## What is Titan?

Titan is not a trading bot. It's a **systematic trading intelligence platform** that:

- Generates trade signals with confidence scores
- Classifies market regimes automatically
- Learns from historical decisions
- Operates 24/7 with self-healing infrastructure
- Communicates naturally — just talk to it

**Core Principle:** Capital preservation > Large profits. A 60% win rate with steady gains beats a 40% win rate chasing big wins.

---

## 🚀 Features

### Market Intelligence
- 📊 Multi-timeframe analysis (4H, 1H, 15m)
- 📈 Signal generation with confidence scoring
- 🔄 Automatic regime detection (Trending/Ranging/High Volatility)
- 📉 Setup classification (Continuation/Pullback/Breakout)
- 📉 ATR-based volatility filtering

### Learning Engine
- 📋 Weekly performance reviews
- 📉 Confidence calibration analysis
- 🎯 Feature importance tracking
- 📊 Rolling performance windows (20/50/100 trades)
- 🔍 Signal explanation

### Operations Layer
- ❤️ Health monitoring (6 subsystems, 5-minute checks)
- 🔧 Self-healing recovery engine (15 incident handlers)
- 🎛️ 9-state system machine
- 📝 Comprehensive audit logging

### Conversational Interface
- 💬 Natural language commands — just talk to Titan
- Examples:
  - *"What's BTC doing?"*
  - *"How's paper trading?"*
  - *"Show me the weekly report"*

---

## 📁 Architecture

```
titanbot/
├── bot/                    # Telegram interface
│   └── handlers/          # Commands & conversations
├── core/                  # Business logic
│   ├── state_manager.py   # System states
│   ├── health_monitor.py  # Health checks
│   ├── recovery_engine.py # Self-healing
│   └── learning_engine.py # Analytics
├── engines/              # Trading algorithms
│   ├── alpha_trendflow.py # Signal generation
│   ├── regime_classifier.py
│   └── confidence_engine.py
├── providers/            # External integrations
│   ├── ai_provider.py     # LLM integration
│   └── market_provider.py # Exchange data
├── services/             # Utilities
│   └── chart_renderer.py  # Visual signals
└── db/                   # Data persistence
```

---

## 🎮 Commands

### Quick Start
| Command | Description |
|---------|-------------|
| `/start` | Welcome to Titan |
| `/help` | List all commands |
| `/status` | Your account status |

### Market Intelligence
| Command | Description |
|---------|-------------|
| `/signal BTCUSDT` | Generate trade signal |
| `/regime BTCUSDT` | Check market regime |
| `/score BTCUSDT` | View confidence breakdown |

### Analysis & Learning
| Command | Description |
|---------|-------------|
| `/journal` | Recent signals |
| `/weekly_review` | Weekly performance |
| `/calibration` | Confidence analysis |
| `/explain <id>` | Signal explanation |

### Operations (Read-Only)
| Command | Description |
|---------|-------------|
| `/health` | Quick health check |
| `/health_report` | Full health report |
| `/system_state` | Current system state |
| `/diagnostics` | Full diagnostic report |

### Administration
| Command | Description |
|---------|-------------|
| `/authorize PIN` | Admin login |
| `/dashboard` | System overview |
| `/pending` | Pending approvals |
| `/approve <id>` | Approve user |

---

## 💬 Conversational Mode

Titan understands natural language. Just chat!

**Examples:**
```
You: what's BTC doing?
Titan: BTCUSDT showing strength 📈
       Signal: LONG (Score: 32/40)
       Setup: TREND PULLBACK
       Confidence: High

You: how's the system?
Titan: ✅ System Health: 95%
       Status: HEALTHY
       Titan State: READY
       All systems operational.

You: show me the weekly report
Titan: 📊 Weekly Review
       Total Trades: 24
       Win Rate: 62.5%
       Expectancy: +1.2%
       Best Pair: BTCUSDT
```

---

## 🔧 Setup

### Requirements
- Python 3.10+
- Telegram Bot Token
- Railway account (for deployment)

### Environment Variables
```env
BOT_TOKEN=your_telegram_bot_token
DB_PATH=./data/titanbot.db
DATA_SOURCE=kraken  # or binance, coinbase, etc.
```

### Installation
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your BOT_TOKEN to .env
python main.py
```

---

## 📊 Wave Status

| Wave | Name | Status |
|------|------|--------|
| 1 | Foundation | ✅ Complete |
| 2A | Market Intelligence | ✅ Complete |
| 2B | Truth Engine | ✅ Complete |
| 2C | Learning Engine | ✅ Complete |
| 2D | News Intelligence | 🔲 Pending |
| 2E | Historical Replay | 🔲 Pending |
| 3 | Paper Trading | 🔲 Pending |
| 4 | Live Trading | 🔲 Pending |

---

## 📖 Documentation

- [Engineering Specification](docs/TSD-001-TITAN-ENGINEERING-SPECIFICATION.md) — Complete roadmap
- [Operational Playbook](docs/OPERATIONAL_PLAYBOOK.md) — System runbook
- [Operational Brief](docs/TITAN_OPERATIONAL_BRIEF.md) — Survival trading rules

---

## 🛡️ Safety Features

### Risk Management
- Max 2% risk per trade
- Max 50% portfolio exposure
- Automatic drawdown protection

### Failure Recovery
- 15 automated recovery procedures
- Health monitoring with alerts
- No silent failures

### Survival Rules
```
3 consecutive losses → Safe Mode (reduce size 50%)
5 consecutive losses → Stop, require approval
10% drawdown → Full stop
```

---

## 🤝 Contributing

This is a private project. For questions, contact the team.

---

## 📝 License

Private — All rights reserved

---

**Built with ❤️ for systematic trading**

*Titan — Survive. Learn. Adapt.*
