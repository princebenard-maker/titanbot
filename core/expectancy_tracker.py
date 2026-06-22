"""
expectancy_tracker.py - TITAN Wave 2B
Tracks whether confidence scores predict
outcomes correctly. Core truth engine.
"""
import logging
from db.database import execute_read, execute_read_one

logger = logging.getLogger(__name__)

async def calculate_expectancy() -> dict:
    """Calculate expectancy per confidence band."""
    result = {}
    bands = [
        ('26-30', 26, 30),
        ('30-35', 30, 35),
        ('35-40', 35, 40)
    ]
    for band_name, low, high in bands:
        if high == 40:
            rows = await execute_read(
                """SELECT outcome FROM signals
                   WHERE score >= ? AND score <= 40
                   AND outcome != 'PENDING'""",
                (low,)
            )
        else:
            rows = await execute_read(
                """SELECT outcome FROM signals
                   WHERE score >= ? AND score < ?
                   AND outcome != 'PENDING'""",
                (low, high)
            )
        total = len(rows)
        wins = sum(1 for r in rows if r['outcome'] == 'WIN')
        win_rate = (wins/total*100) if total > 0 else 0
        result[band_name] = {
            'total': total,
            'wins': wins,
            'win_rate': round(win_rate, 1),
            'expectancy': round(win_rate/100, 3)
        }
    return result

async def get_overall_stats() -> dict:
    """Get overall signal performance stats."""
    total_row = await execute_read_one(
        "SELECT COUNT(*) as count FROM signals"
    )
    pending_row = await execute_read_one(
        """SELECT COUNT(*) as count FROM signals
           WHERE outcome = 'PENDING'"""
    )
    win_row = await execute_read_one(
        """SELECT COUNT(*) as count FROM signals
           WHERE outcome = 'WIN'"""
    )
    total = total_row['count'] if total_row else 0
    pending = pending_row['count'] if pending_row else 0
    completed = total - pending
    wins = win_row['count'] if win_row else 0
    win_rate = (wins/completed*100) if completed > 0 else 0
    return {
        'total_signals': total,
        'completed': completed,
        'pending': pending,
        'wins': wins,
        'win_rate': round(win_rate, 1)
    }
