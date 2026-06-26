"""
learning_engine.py - WAVE 2C
Titan Learning Engine
Analyzes historical decisions to improve understanding.
"""
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# Failure Classification Types
class FailureType:
    REGIME_MISMATCH = "REGIME_MISMATCH"
    ENTRY_TOO_EARLY = "ENTRY_TOO_EARLY"
    ENTRY_TOO_LATE = "ENTRY_TOO_LATE"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"
    LOW_VOLUME = "LOW_VOLUME"
    NEWS_EVENT = "NEWS_EVENT"
    STOP_HUNT = "STOP_HUNT"
    UNKNOWN = "UNKNOWN"


@dataclass
class WeeklyStats:
    """Weekly performance statistics."""
    week_start: datetime
    week_end: datetime
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    expectancy: float = 0.0
    avg_confidence: float = 0.0
    avg_atr: float = 0.0
    by_regime: dict = field(default_factory=dict)
    by_setup: dict = field(default_factory=dict)
    by_pair: dict = field(default_factory=dict)
    best_pair: str = ""
    worst_pair: str = ""
    best_streak: int = 0
    worst_streak: int = 0


@dataclass
class ConfidenceCalibration:
    """Confidence level performance data."""
    range_35_40: dict = field(default_factory=lambda: {"total": 0, "wins": 0, "rate": 0.0})
    range_30_34: dict = field(default_factory=lambda: {"total": 0, "wins": 0, "rate": 0.0})
    range_25_29: dict = field(default_factory=lambda: {"total": 0, "wins": 0, "rate": 0.0})
    range_20_24: dict = field(default_factory=lambda: {"total": 0, "wins": 0, "rate": 0.0})


@dataclass
class FeatureImportance:
    """Feature contribution data."""
    trend_alignment: float = 0.0
    price_action: float = 0.0
    volume: float = 0.0
    macd: float = 0.0
    atr: float = 0.0
    news: float = 0.0


@dataclass
class RollingPerformance:
    """Rolling window performance."""
    window_20: dict = field(default_factory=lambda: {"count": 0, "wins": 0, "expectancy": 0.0, "streak": 0})
    window_50: dict = field(default_factory=lambda: {"count": 0, "wins": 0, "expectancy": 0.0, "streak": 0})
    window_100: dict = field(default_factory=lambda: {"count": 0, "wins": 0, "expectancy": 0.0, "streak": 0})
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    consecutive_wins: int = 0
    max_consecutive_wins: int = 0


class LearningEngine:
    """
    Titan Learning Engine.
    Analyzes historical decisions without predicting prices.
    """
    
    def __init__(self):
        self._calibration: Optional[ConfidenceCalibration] = None
        self._feature_importance: Optional[FeatureImportance] = None
        self._rolling: RollingPerformance = RollingPerformance()
    
    async def get_weekly_review(self, weeks_back: int = 1) -> WeeklyStats:
        """Generate weekly performance review."""
        from db.database import execute_read
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        signals = await execute_read(
            """SELECT * FROM signals 
               WHERE timestamp >= ? AND outcome != 'PENDING'
               ORDER BY timestamp DESC""",
            (start_date.isoformat(),)
        )
        
        if not signals:
            return WeeklyStats(week_start=start_date, week_end=end_date)
        
        stats = WeeklyStats(week_start=start_date, week_end=end_date)
        
        # Basic stats
        stats.total_trades = len(signals)
        stats.wins = sum(1 for s in signals if s.get('outcome') == 'WIN')
        stats.losses = sum(1 for s in signals if s.get('outcome') == 'LOSS')
        
        if stats.total_trades > 0:
            stats.win_rate = (stats.wins / stats.total_trades) * 100
        
        # Expectancy
        total_pnl = sum(s.get('pnl_pct', 0) for s in signals)
        stats.expectancy = total_pnl / stats.total_trades if stats.total_trades > 0 else 0
        
        # Averages
        confidence_scores = [s.get('score', 0) for s in signals if s.get('score')]
        if confidence_scores:
            stats.avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Calculate ATR from breakdown if available
        atr_values = []
        for s in signals:
            try:
                breakdown = json.loads(s.get('score_breakdown', '{}'))
                if 'ATR' in breakdown:
                    atr_values.append(breakdown['ATR'])
            except:
                pass
        if atr_values:
            stats.avg_atr = sum(atr_values) / len(atr_values)
        
        # By Regime
        regime_stats = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0})
        for s in signals:
            regime = s.get('regime', 'UNKNOWN')
            regime_stats[regime]["total"] += 1
            if s.get('outcome') == 'WIN':
                regime_stats[regime]["wins"] += 1
            else:
                regime_stats[regime]["losses"] += 1
        
        for regime, data in regime_stats.items():
            total = data["total"]
            wins = data["wins"]
            stats.by_regime[regime] = {
                "total": total,
                "wins": wins,
                "win_rate": (wins / total * 100) if total > 0 else 0
            }
        
        # By Setup Type
        setup_stats = defaultdict(lambda: {"total": 0, "wins": 0})
        for s in signals:
            setup = s.get('setup_type', 'N/A')
            setup_stats[setup]["total"] += 1
            if s.get('outcome') == 'WIN':
                setup_stats[setup]["wins"] += 1
        
        for setup, data in setup_stats.items():
            total = data["total"]
            wins = data["wins"]
            stats.by_setup[setup] = {
                "total": total,
                "wins": wins,
                "win_rate": (wins / total * 100) if total > 0 else 0
            }
        
        # By Pair
        pair_stats = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0})
        for s in signals:
            pair = s.get('symbol', 'UNKNOWN')
            pair_stats[pair]["total"] += 1
            pair_stats[pair]["pnl"] += s.get('pnl_pct', 0)
            if s.get('outcome') == 'WIN':
                pair_stats[pair]["wins"] += 1
            else:
                pair_stats[pair]["losses"] += 1
        
        for pair, data in pair_stats.items():
            total = data["total"]
            wins = data["wins"]
            stats.by_pair[pair] = {
                "total": total,
                "wins": wins,
                "losses": data["losses"],
                "win_rate": (wins / total * 100) if total > 0 else 0,
                "pnl": data["pnl"]
            }
        
        # Best/Worst Pair
        if pair_stats:
            sorted_pairs = sorted(pair_stats.items(), key=lambda x: x[1]["pnl"], reverse=True)
            stats.best_pair = sorted_pairs[0][0] if sorted_pairs else ""
            stats.worst_pair = sorted_pairs[-1][0] if sorted_pairs else ""
        
        # Streaks
        outcomes = [s.get('outcome') for s in reversed(signals)]
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        temp_loss_streak = 0
        
        for outcome in outcomes:
            if outcome == 'WIN':
                current_streak = current_streak + 1 if outcomes.index(outcome) > 0 and outcomes[outcomes.index(outcome)-1] == 'WIN' else 1
                max_win_streak = max(max_win_streak, current_streak)
                temp_loss_streak = 0
            elif outcome == 'LOSS':
                temp_loss_streak += 1
                max_loss_streak = max(max_loss_streak, temp_loss_streak)
        
        stats.best_streak = max_win_streak
        stats.worst_streak = max_loss_streak
        
        return stats
    
    async def analyze_confidence_calibration(self) -> ConfidenceCalibration:
        """Analyze if confidence scores correlate with outcomes."""
        from db.database import execute_read
        
        signals = await execute_read(
            """SELECT * FROM signals 
               WHERE outcome != 'PENDING'
               ORDER BY timestamp DESC
               LIMIT 500"""
        )
        
        calibration = ConfidenceCalibration()
        
        for s in signals:
            score = s.get('score', 0)
            outcome = s.get('outcome', '')
            
            if 35 <= score <= 40:
                calibration.range_35_40["total"] += 1
                if outcome == 'WIN':
                    calibration.range_35_40["wins"] += 1
            elif 30 <= score <= 34:
                calibration.range_30_34["total"] += 1
                if outcome == 'WIN':
                    calibration.range_30_34["wins"] += 1
            elif 25 <= score <= 29:
                calibration.range_25_29["total"] += 1
                if outcome == 'WIN':
                    calibration.range_25_29["wins"] += 1
            elif 20 <= score <= 24:
                calibration.range_20_24["total"] += 1
                if outcome == 'WIN':
                    calibration.range_20_24["wins"] += 1
        
        # Calculate rates
        for range_data in [calibration.range_35_40, calibration.range_30_34, 
                          calibration.range_25_29, calibration.range_20_24]:
            total = range_data["total"]
            if total > 0:
                range_data["rate"] = (range_data["wins"] / total) * 100
        
        self._calibration = calibration
        return calibration
    
    async def analyze_feature_importance(self) -> FeatureImportance:
        """Measure contribution of each scoring component."""
        from db.database import execute_read
        
        signals = await execute_read(
            """SELECT * FROM signals 
               WHERE outcome != 'PENDING'
               ORDER BY timestamp DESC
               LIMIT 200"""
        )
        
        importance = FeatureImportance()
        
        # Count wins where each component was positive
        component_wins = {
            "trend": 0, "price_action": 0, "volume": 0, 
            "macd": 0, "atr": 0, "news": 0
        }
        total_wins = 0
        
        for s in signals:
            if s.get('outcome') != 'WIN':
                continue
            total_wins += 1
            
            try:
                breakdown = json.loads(s.get('score_breakdown', '{}'))
                
                # Check each component (simplified - assumes breakdown contains component scores)
                if breakdown.get('Trend', 0) > 5:
                    component_wins["trend"] += 1
                if breakdown.get('Price Action', 0) > 5:
                    component_wins["price_action"] += 1
                if breakdown.get('Volume', 0) > 5:
                    component_wins["volume"] += 1
                if breakdown.get('MACD', 0) > 5:
                    component_wins["macd"] += 1
                if breakdown.get('ATR', 0) > 5:
                    component_wins["atr"] += 1
                if breakdown.get('News', 0) > 5:
                    component_wins["news"] += 1
            except:
                pass
        
        # Calculate percentages
        if total_wins > 0:
            importance.trend_alignment = (component_wins["trend"] / total_wins) * 100
            importance.price_action = (component_wins["price_action"] / total_wins) * 100
            importance.volume = (component_wins["volume"] / total_wins) * 100
            importance.macd = (component_wins["macd"] / total_wins) * 100
            importance.atr = (component_wins["atr"] / total_wins) * 100
            importance.news = (component_wins["news"] / total_wins) * 100
        
        self._feature_importance = importance
        return importance
    
    async def update_rolling_performance(self, new_outcome: Optional[str] = None) -> RollingPerformance:
        """Update rolling performance statistics."""
        from db.database import execute_read
        
        # Get recent signals
        signals_20 = await execute_read(
            """SELECT * FROM signals WHERE outcome != 'PENDING' ORDER BY id DESC LIMIT 20"""
        )
        signals_50 = await execute_read(
            """SELECT * FROM signals WHERE outcome != 'PENDING' ORDER BY id DESC LIMIT 50"""
        )
        signals_100 = await execute_read(
            """SELECT * FROM signals WHERE outcome != 'PENDING' ORDER BY id DESC LIMIT 100"""
        )
        
        def calc_stats(signals):
            if not signals:
                return {"count": 0, "wins": 0, "expectancy": 0.0}
            wins = sum(1 for s in signals if s.get('outcome') == 'WIN')
            pnl = sum(s.get('pnl_pct', 0) for s in signals)
            return {
                "count": len(signals),
                "wins": wins,
                "win_rate": (wins / len(signals)) * 100 if signals else 0,
                "expectancy": pnl / len(signals) if signals else 0
            }
        
        self._rolling.window_20 = calc_stats(signals_20)
        self._rolling.window_50 = calc_stats(signals_50)
        self._rolling.window_100 = calc_stats(signals_100)
        
        # Calculate streaks from all signals
        all_signals = await execute_read(
            """SELECT outcome FROM signals WHERE outcome != 'PENDING' ORDER BY id DESC LIMIT 100"""
        )
        
        if all_signals:
            outcomes = [s['outcome'] for s in all_signals]
            current_loss_streak = 0
            current_win_streak = 0
            
            for outcome in outcomes:
                if outcome == 'WIN':
                    current_win_streak += 1
                    current_loss_streak = 0
                else:
                    current_loss_streak += 1
                    current_win_streak = 0
            
            self._rolling.consecutive_losses = current_loss_streak
            self._rolling.consecutive_wins = current_win_streak
            self._rolling.max_consecutive_losses = max(
                self._rolling.max_consecutive_losses, current_loss_streak
            )
            self._rolling.max_consecutive_wins = max(
                self._rolling.max_consecutive_wins, current_win_streak
            )
        
        return self._rolling
    
    async def check_degradation(self, threshold: float = -1.0) -> dict:
        """Check if rolling performance is degrading."""
        rolling = self._rolling
        
        warnings = []
        
        # Check expectancy degradation
        if rolling.window_20["expectancy"] < threshold:
            warnings.append({
                "type": "expectancy",
                "window": "20",
                "value": rolling.window_20["expectancy"],
                "threshold": threshold
            })
        
        if rolling.window_50["expectancy"] < threshold:
            warnings.append({
                "type": "expectancy",
                "window": "50",
                "value": rolling.window_50["expectancy"],
                "threshold": threshold
            })
        
        return {
            "degraded": len(warnings) > 0,
            "warnings": warnings,
            "rolling": rolling.__dict__
        }
    
    async def classify_failure(self, signal_id: int, failure_type: str) -> bool:
        """Classify a losing trade with a failure reason."""
        from db.database import execute_write
        
        valid_types = [
            FailureType.REGIME_MISMATCH, FailureType.ENTRY_TOO_EARLY,
            FailureType.ENTRY_TOO_LATE, FailureType.VOLATILITY_SPIKE,
            FailureType.LOW_VOLUME, FailureType.NEWS_EVENT,
            FailureType.STOP_HUNT, FailureType.UNKNOWN
        ]
        
        if failure_type not in valid_types:
            logger.warning(f"Invalid failure type: {failure_type}")
            return False
        
        # Store failure classification in score_breakdown JSON
        await execute_write(
            """UPDATE signals SET score_breakdown = 
               COALESCE(score_breakdown, '{}') || ? WHERE id = ?""",
            (json.dumps({"failure_type": failure_type}), signal_id)
        )
        
        logger.info(f"Failure classified: signal {signal_id} = {failure_type}")
        return True
    
    async def get_failure_analysis(self) -> dict:
        """Get analysis of failure types."""
        from db.database import execute_read
        
        signals = await execute_read(
            """SELECT * FROM signals WHERE outcome = 'LOSS'"""
        )
        
        failure_counts = defaultdict(int)
        
        for s in signals:
            try:
                breakdown = json.loads(s.get('score_breakdown', '{}'))
                failure_type = breakdown.get('failure_type', FailureType.UNKNOWN)
                failure_counts[failure_type] += 1
            except:
                failure_counts[FailureType.UNKNOWN] += 1
        
        total_losses = len(signals)
        failure_analysis = {}
        
        for failure_type, count in failure_counts.items():
            failure_analysis[failure_type] = {
                "count": count,
                "percentage": (count / total_losses * 100) if total_losses > 0 else 0
            }
        
        return failure_analysis
    
    async def get_explanation(self, signal_id: int) -> Optional[dict]:
        """Get full explanation of a signal decision."""
        from db.database import execute_read_one
        
        signal = await execute_read_one(
            """SELECT * FROM signals WHERE id = ?""",
            (signal_id,)
        )
        
        if not signal:
            return None
        
        try:
            breakdown = json.loads(signal.get('score_breakdown', '{}'))
            reasons = json.loads(signal.get('score_breakdown', '{}')).get('reasons', {})
        except:
            breakdown = {}
            reasons = {}
        
        explanation = {
            "signal_id": signal_id,
            "timestamp": signal.get('timestamp'),
            "symbol": signal.get('symbol'),
            "signal": signal.get('signal'),
            "score": signal.get('score'),
            "regime": signal.get('regime'),
            "setup_type": signal.get('setup_type', 'N/A'),
            "score_breakdown": breakdown,
            "reason": signal.get('signal'),  # The reasoning is in the signal generation
            "outcome": signal.get('outcome'),
            "pnl_pct": signal.get('pnl_pct', 0),
            "entry_price": signal.get('entry_price', 0),
            "exit_price": signal.get('exit_price', 0),
        }
        
        # Add failure type if loss
        if signal.get('outcome') == 'LOSS':
            explanation["failure_type"] = breakdown.get('failure_type', FailureType.UNKNOWN)
        
        return explanation


# Global learning engine instance
_learning_engine: Optional[LearningEngine] = None


def get_learning_engine() -> LearningEngine:
    """Get the global learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine
