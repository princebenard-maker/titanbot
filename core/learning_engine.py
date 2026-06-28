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


class LearningMode:
    """Learning mode types."""
    CONSERVATIVE = "CONSERVATIVE"      # High confidence only, small size
    MODERATE = "MODERATE"              # Medium confidence, medium size
    AGGRESSIVE = "AGGRESSIVE"          # Lower confidence OK, larger size
    PAPER_TESTING = "PAPER_TESTING"    # Test new strategies
    RECOVERY = "RECOVERY"              # After losses, very conservative


class LearningEngine:
    """
    Titan Learning Engine.
    Analyzes historical decisions without predicting prices.
    """
    
    # Mode configurations
    MODE_CONFIGS = {
        LearningMode.CONSERVATIVE: {
            "min_confidence": 35,
            "max_risk_percent": 1.0,
            "max_positions": 1,
        },
        LearningMode.MODERATE: {
            "min_confidence": 28,
            "max_risk_percent": 2.0,
            "max_positions": 2,
        },
        LearningMode.AGGRESSIVE: {
            "min_confidence": 22,
            "max_risk_percent": 3.0,
            "max_positions": 3,
        },
        LearningMode.PAPER_TESTING: {
            "min_confidence": 15,
            "max_risk_percent": 2.0,
            "max_positions": 1,
        },
        LearningMode.RECOVERY: {
            "min_confidence": 38,
            "max_risk_percent": 0.5,
            "max_positions": 1,
        },
    }
    
    def __init__(self):
        self._calibration: Optional[ConfidenceCalibration] = None
        self._feature_importance: Optional[FeatureImportance] = None
        self._rolling: RollingPerformance = RollingPerformance()
        self._current_mode: str = LearningMode.MODERATE
        self._mode_reason: str = "Default mode on startup"
    
    def get_mode_config(self) -> dict:
        """Get current mode configuration."""
        return {
            "mode": self._current_mode,
            "reason": self._mode_reason,
            **self.MODE_CONFIGS.get(self._current_mode, self.MODE_CONFIGS[LearningMode.MODERATE])
        }
    
    async def get_recommended_mode(self) -> str:
        """Analyze performance and recommend a learning mode."""
        from db.database import execute_read
        
        # Get recent signals
        signals = await execute_read(
            """SELECT outcome FROM signals WHERE outcome != 'PENDING' ORDER BY id DESC LIMIT 20"""
        )
        
        if not signals:
            return LearningMode.MODERATE
        
        wins = sum(1 for s in signals if s.get('outcome') == 'WIN')
        losses = sum(1 for s in signals if s.get('outcome') == 'LOSS')
        total = wins + losses
        
        if total < 5:
            return LearningMode.PAPER_TESTING
        
        win_rate = (wins / total) * 100 if total > 0 else 0
        
        # Calculate recent expectancy
        pnl_values = [s.get('pnl_pct', 0) for s in signals]
        expectancy = sum(pnl_values) / len(pnl_values) if pnl_values else 0
        
        # Check consecutive losses
        outcomes = [s.get('outcome') for s in reversed(signals)]
        current_loss_streak = 0
        for outcome in outcomes:
            if outcome == 'WIN':
                break
            current_loss_streak += 1
        
        # Determine mode based on performance
        if current_loss_streak >= 5:
            self._mode_reason = f"5+ consecutive losses detected"
            return LearningMode.RECOVERY
        elif win_rate < 35 and expectancy < -0.5:
            self._mode_reason = f"Poor performance: {win_rate:.0f}% WR, {expectancy:.2f}% expectancy"
            return LearningMode.CONSERVATIVE
        elif win_rate >= 55 and expectancy >= 1.0:
            self._mode_reason = f"Strong performance: {win_rate:.0f}% WR, {expectancy:.2f}% expectancy"
            return LearningMode.AGGRESSIVE
        elif current_loss_streak >= 3:
            self._mode_reason = f"3 consecutive losses detected"
            return LearningMode.RECOVERY
        else:
            self._mode_reason = f"Normal performance: {win_rate:.0f}% WR, {expectancy:.2f}% expectancy"
            return LearningMode.MODERATE
    
    async def set_mode(self, mode: str) -> bool:
        """Manually set learning mode."""
        valid_modes = [LearningMode.CONSERVATIVE, LearningMode.MODERATE, 
                      LearningMode.AGGRESSIVE, LearningMode.PAPER_TESTING, 
                      LearningMode.RECOVERY]
        
        if mode not in valid_modes:
            return False
        
        self._current_mode = mode
        self._mode_reason = f"Manually set to {mode}"
        logger.info(f"Learning mode changed to {mode}")
        return True
    
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
    
    def format_weekly_review(self, stats: WeeklyStats) -> str:
        """Format weekly review for Telegram display."""
        lines = [
            "📊 *WEEKLY PERFORMANCE REPORT*",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Period: {stats.week_start.strftime('%b %d')} - {stats.week_end.strftime('%b %d')}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Total Trades: *{stats.total_trades}*",
            f"Wins: *{stats.wins}* | Losses: *{stats.losses}*",
            f"Win Rate: *{stats.win_rate:.1f}%*",
            f"Expectancy: *{stats.expectancy:.2f}%*",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Avg Confidence: *{stats.avg_confidence:.1f}*",
            f"Avg ATR: *{stats.avg_atr:.2f}%*",
        ]
        
        if stats.best_pair:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"🏆 Best Pair: *{stats.best_pair}*")
            lines.append(f"😰 Worst Pair: *{stats.worst_pair}*")
        
        if stats.by_regime:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("*By Regime:*")
            for regime, data in stats.by_regime.items():
                lines.append(f"  {regime}: {data['win_rate']:.0f}% ({data['total']} trades)")
        
        if stats.by_setup:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("*By Setup:*")
            for setup, data in stats.by_setup.items():
                lines.append(f"  {setup}: {data['win_rate']:.0f}% ({data['total']} trades)")
        
        return "\n".join(lines)
    
    def format_calibration(self, calibration: ConfidenceCalibration) -> str:
        """Format confidence calibration for Telegram."""
        lines = [
            "🎯 *CONFIDENCE CALIBRATION*",
            "━━━━━━━━━━━━━━━━━━━━",
            "*How well does our confidence match actual win rate?*",
            "━━━━━━━━━━━━━━━━━━━━",
        ]
        
        ranges = [
            ("35-40", calibration.range_35_40),
            ("30-34", calibration.range_30_34),
            ("25-29", calibration.range_25_29),
            ("20-24", calibration.range_20_24),
        ]
        
        for label, data in ranges:
            actual = data.get('rate', 0)
            expected_low = int(label.split('-')[0])
            expected_high = int(label.split('-')[1])
            expected_mid = (expected_low + expected_high) / 2
            
            diff = actual - expected_mid
            indicator = "🟢" if abs(diff) < 5 else ("🔴" if diff < 0 else "🟡")
            
            lines.append(f"{indicator} Score {label}: *{actual:.1f}%* actual (expected ~{expected_mid:.0f}%)")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🟢 = Well calibrated | 🔴 = Overconfident | 🟡 = Underconfident")
        
        return "\n".join(lines)
    
    def format_feature_importance(self, importance: FeatureImportance) -> str:
        """Format feature importance for Telegram."""
        features = [
            ("Trend Alignment", importance.trend_alignment),
            ("Price Action", importance.price_action),
            ("Volume", importance.volume),
            ("MACD", importance.macd),
            ("ATR", importance.atr),
            ("News", importance.news),
        ]
        
        sorted_features = sorted(features, key=lambda x: x[1], reverse=True)
        
        lines = [
            "🔍 *FEATURE IMPORTANCE*",
            "━━━━━━━━━━━━━━━━━━━━",
            "*Which signals contribute most to wins?*",
            "━━━━━━━━━━━━━━━━━━━━",
        ]
        
        for name, value in sorted_features:
            bar = "█" * int(value / 5) + "░" * (20 - int(value / 5))
            lines.append(f"{name:18} {bar} *{value:.1f}%*")
        
        return "\n".join(lines)
    
    def format_mode_status(self, mode_config: dict, recommended: str) -> str:
        """Format learning mode status for Telegram."""
        emoji = {
            "CONSERVATIVE": "🛡️",
            "MODERATE": "⚖️",
            "AGGRESSIVE": "🚀",
            "PAPER_TESTING": "🧪",
            "RECOVERY": "🏥",
        }
        
        mode_emoji = emoji.get(mode_config['mode'], "⚙️")
        
        lines = [
            f"{mode_emoji} *LEARNING MODE: {mode_config['mode']}*",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📝 Reason: {mode_config['reason']}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"Min Confidence: *{mode_config['min_confidence']}*",
            f"Max Risk: *{mode_config['max_risk_percent']}%*",
            f"Max Positions: *{mode_config['max_positions']}*",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🤖 Recommended: *{recommended}*",
        ]
        
        return "\n".join(lines)


# Global learning engine instance
_learning_engine: Optional[LearningEngine] = None


def get_learning_engine() -> LearningEngine:
    """Get the global learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine
