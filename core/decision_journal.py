"""
decision_journal.py - TITAN Wave 2B
Stores every signal with full context.
Append only. Never delete signals.
"""
import json
import logging
from datetime import datetime
from db.database import execute_write, execute_read, execute_read_one

logger = logging.getLogger(__name__)

async def save_signal(
    symbol: str,
    signal: str,
    score: int,
    regime: str,
    score_breakdown: dict,
    reasons: dict,
    entry_price: float = 0.0
) -> int:
    details = json.dumps({
        'breakdown': score_breakdown,
        'reasons': reasons
    })
    await execute_write(
        """INSERT INTO signals
           (symbol, signal, score, regime,
            score_breakdown, entry_price)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (symbol, signal, score, regime,
         details, entry_price)
    )
    row = await execute_read_one(
        "SELECT id FROM signals ORDER BY id DESC LIMIT 1"
    )
    signal_id = row['id'] if row else 0
    logger.info(f"Signal saved: {symbol} {signal} {score}/40")
    return signal_id

async def get_recent_signals(limit: int = 20) -> list:
    limit = min(limit, 100)
    return await execute_read(
        """SELECT * FROM signals
           ORDER BY timestamp DESC LIMIT ?""",
        (limit,)
    )

async def update_signal_outcome(
    signal_id: int,
    outcome: str,
    exit_price: float,
    pnl_pct: float
) -> None:
    await execute_write(
        """UPDATE signals SET outcome=?,
           exit_price=?, pnl_pct=?
           WHERE id=?""",
        (outcome, exit_price, pnl_pct, signal_id)
    )

async def get_signals_by_band() -> dict:
    bands = {
        '26-30': await execute_read(
            """SELECT * FROM signals
               WHERE score >= 26 AND score < 30
               AND outcome != 'PENDING'"""
        ),
        '30-35': await execute_read(
            """SELECT * FROM signals
               WHERE score >= 30 AND score < 35
               AND outcome != 'PENDING'"""
        ),
        '35-40': await execute_read(
            """SELECT * FROM signals
               WHERE score >= 35
               AND outcome != 'PENDING'"""
        )
    }
    return bands
