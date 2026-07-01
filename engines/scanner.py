"""
scanner.py - TITAN V1 AUTONOMOUS MARKET SCANNER + EXECUTION
Scans watchlist, evaluates opportunities, executes trades.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ScanStatus(Enum):
    """Scan result status."""
    SCAN = "SCAN"
    TRADE = "TRADE"
    REJECT = "REJECT"
    WAIT = "WAIT"
    LOW_VOLUME = "LOW_VOLUME"
    BAD_REGIME = "BAD_REGIME"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


@dataclass
class ScanResult:
    """Result of market scan for a pair."""
    pair: str
    timestamp: datetime
    status: ScanStatus
    score: int = 0
    regime: str = "UNKNOWN"
    atr: float = 0.0
    atr_pct: float = 0.0
    volume_ratio: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_reward: float = 0.0
    rejection_reasons: List[str] = field(default_factory=list)
    confidence_breakdown: Dict[str, int] = field(default_factory=dict)


class MarketScanner:
    """
    Autonomous market scanner with auto-execution.
    Scans watchlist, evaluates opportunities, executes paper trades.
    """
    
    # Default watchlist
    DEFAULT_WATCHLIST = [
        "BTCUSDT",
        "ETHUSDT", 
        "SOLUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "LINKUSDT",
        "AVAXUSDT",
        "SUIUSDT",
        "NEARUSDT",
        "ATOMUSDT",
    ]
    
    # Volume thresholds
    MIN_VOLUME_RATIO = 0.5  # 50% of 20-day average
    GOOD_VOLUME_RATIO = 1.2  # 120% of average = good
    
    def __init__(self):
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        self._execution_task: Optional[asyncio.Task] = None
        self._watchlist: List[str] = self.DEFAULT_WATCHLIST.copy()
        self._scan_interval = 900  # 15 minutes
        self._last_scan: Dict[str, datetime] = {}
        self._scan_cache: Dict[str, ScanResult] = {}
        self._lock = asyncio.Lock()
        
        # Execution tracking
        self._trades_executed_today = 0
        self._last_execution_reset = datetime.utcnow()
        
        # Stats
        self.total_scans = 0
        self.trade_signals = 0
        self.trades_executed = 0
        self.rejections = 0
    
    @property
    def watchlist(self) -> List[str]:
        return self._watchlist.copy()
    
    async def start(self):
        """Start autonomous scanning and execution."""
        if self._running:
            return
        
        self._running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        self._execution_task = asyncio.create_task(self._execution_loop())
        logger.info(f"Market scanner started with auto-execution. Watching {len(self._watchlist)} pairs")
    
    async def stop(self):
        """Stop autonomous scanning."""
        self._running = False
        
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
        
        if self._execution_task:
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Market scanner stopped")
    
    async def add_to_watchlist(self, pair: str):
        """Add pair to watchlist."""
        pair = pair.upper()
        if pair not in self._watchlist:
            self._watchlist.append(pair)
            logger.info(f"Added {pair} to watchlist")
    
    async def remove_from_watchlist(self, pair: str):
        """Remove pair from watchlist."""
        pair = pair.upper()
        if pair in self._watchlist:
            self._watchlist.remove(pair)
            logger.info(f"Removed {pair} from watchlist")
    
    async def _get_market_data(self, pair: str) -> Dict:
        """Get market data for a pair."""
        try:
            from data.market_fetcher import fetch_ohlcv
            import pandas as pd
            
            # Fetch 1h data for analysis
            df_1h = await fetch_ohlcv(pair, "1h", limit=100)
            if df_1h.empty:
                return {}
            
            # Calculate ATR
            high = df_1h['high']
            low = df_1h['low']
            close = df_1h['close']
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            # Calculate volume ratio
            current_volume = df_1h['volume'].iloc[-1]  # Latest completed candle
            avg_volume = df_1h['volume'].iloc[-20:].mean()  # Rolling historical average
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Get regime
            from engines.regime_classifier import classify_regime
            regime_result = classify_regime(df_1h)
            regime = regime_result.get("regime", "RANGING")
            atr_pct = regime_result.get("atr_pct", 0)
            
            # Calculate confidence score
            from engines.confidence_engine import calculate_score
            confidence_result = calculate_score(df_1h, regime_result)
            
            return {
                "price": close.iloc[-1],
                "atr": atr,
                "atr_pct": atr_pct,
                "volume_ratio": volume_ratio,
                "regime": regime,
                "regime_result": regime_result,
                "confidence": confidence_result,
            }
        except Exception as e:
            logger.error(f"Error getting market data for {pair}: {e}")
            return {}
    
    async def scan_pair(self, pair: str) -> ScanResult:
        """Scan a single pair and return result."""
        try:
            market = await self._get_market_data(pair)
            
            if not market:
                return ScanResult(
                    pair=pair,
                    timestamp=datetime.utcnow(),
                    status=ScanStatus.REJECT,
                    rejection_reasons=["Market data unavailable"]
                )
            
            regime = market.get("regime", "UNKNOWN")
            confidence = market.get("confidence", {})
            score = confidence.get("total_score", 0)
            breakdown = confidence.get("breakdown", {})
            atr = market.get("atr", 0)
            atr_pct = market.get("atr_pct", 0)
            volume_ratio = market.get("volume_ratio", 1.0)
            current_price = market.get("price", 0)
            
            result = ScanResult(
                pair=pair,
                timestamp=datetime.utcnow(),
                status=ScanStatus.SCAN,
                score=score,
                regime=regime,
                atr=atr,
                atr_pct=atr_pct,
                volume_ratio=volume_ratio,
                entry_price=current_price,
                confidence_breakdown=breakdown
            )
            
            rejection_reasons = []
            
            # Volume check
            if volume_ratio < self.MIN_VOLUME_RATIO:
                rejection_reasons.append(f"Low volume: {volume_ratio:.2f}x average")
                result.status = ScanStatus.LOW_VOLUME
            
            # Regime check
            if regime in ["RANGING", "UNKNOWN"]:
                rejection_reasons.append(f"Bad regime: {regime}")
                if result.status == ScanStatus.SCAN:
                    result.status = ScanStatus.BAD_REGIME
            
            # Confidence check
            if score < 28:
                rejection_reasons.append(f"Low confidence: {score}/40")
                if result.status == ScanStatus.SCAN:
                    result.status = ScanStatus.LOW_CONFIDENCE
            
            # Trade evaluation
            if result.status == ScanStatus.SCAN:
                if score >= 28 and regime in ["TRENDING_BULL"]:
                    result.status = ScanStatus.TRADE
                    self.trade_signals += 1
                else:
                    result.status = ScanStatus.REJECT
                    rejection_reasons.append("Does not meet trade criteria")
            
            result.rejection_reasons = rejection_reasons
            
            # Calculate SL/TP
            if current_price > 0 and atr > 0:
                sl_distance = atr * 1.5
                tp_distance = atr * 2.5
                result.stop_loss = current_price - sl_distance
                result.take_profit = current_price + tp_distance
                result.risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0
            
            return result
            
        except Exception as e:
            logger.error(f"Scan error for {pair}: {e}")
            return ScanResult(
                pair=pair,
                timestamp=datetime.utcnow(),
                status=ScanStatus.REJECT,
                rejection_reasons=[str(e)]
            )
    
    async def scan_all(self) -> List[ScanResult]:
        """Scan entire watchlist."""
        results = []
        
        for pair in self._watchlist:
            result = await self.scan_pair(pair)
            results.append(result)
            self._last_scan[pair] = datetime.utcnow()
        
        self.total_scans += 1
        return results
    
    async def _can_execute_trade(self) -> tuple[bool, str]:
        """Check if we can execute a new trade."""
        from core.state_manager import get_state_manager
        from broker.paper import get_paper_broker
        from broker.scheduler import get_scheduler
        
        state_manager = get_state_manager()
        broker = get_paper_broker()
        scheduler = get_scheduler()
        
        # Check state
        if not state_manager.can_trade():
            return False, "Trading not allowed by state manager"
        
        # Check if paused
        state_info = state_manager.get_state_info()
        if state_info.get('state') in ['PAUSED', 'SAFE_MODE']:
            return False, f"Trading paused: {state_info.get('state')}"
        
        # Check circuit breaker via scheduler
        account = await broker.get_account()
        can_trade, cb_reason = scheduler.is_trading_allowed(account.consecutive_losses)
        if not can_trade:
            return False, cb_reason
        
        # Check daily trade limit
        if self._trades_executed_today >= 5:
            return False, "Daily trade limit reached (5)"
        
        # Check open positions
        positions = await broker.get_positions()
        if len(positions) >= 3:
            return False, f"Max open positions reached ({len(positions)}/3)"
        
        # Check account
        if account.available_balance < 1.0:
            return False, f"Insufficient balance: ${account.available_balance:.2f}"
        
        return True, "OK"
    
    async def _execute_trade(self, scan_result: ScanResult) -> bool:
        """Execute a paper trade from scan result."""
        try:
            from broker.paper import get_paper_broker
            from core.state_manager import get_state_manager
            from broker.risk_engine import get_risk_engine
            
            broker = get_paper_broker()
            state_manager = get_state_manager()
            risk_engine = get_risk_engine()
            
            # Verify pair not already traded
            existing = await broker.get_position_by_pair(scan_result.pair)
            if existing:
                logger.info(f"{scan_result.pair} already has open position, skipping")
                return False
            
            # Get account balance
            account = await broker.get_account()
            
            # Calculate position size using risk engine
            # Risk engine returns (quantity, risk_amount)
            quantity, risk_amount = risk_engine.calculate_position_size(
                account_balance=account.balance,
                entry_price=scan_result.entry_price,
                stop_loss=scan_result.stop_loss,
                risk_percent=1.5  # 1.5% risk
            )
            
            if quantity <= 0:
                logger.warning(f"Risk engine returned invalid quantity for {scan_result.pair}")
                return False
            
            # Execute trade
            result = await broker.open_position(
                pair=scan_result.pair,
                side="BUY",  # Long for bullish
                entry_price=scan_result.entry_price,
                stop_loss=scan_result.stop_loss,
                take_profit=scan_result.take_profit,
                quantity=quantity,
                risk_percent=1.5,
                regime=scan_result.regime,
                confidence=scan_result.score,
                setup_type="SCANNER_SIGNAL"
            )
            
            if result.success:
                self.trades_executed += 1
                self._trades_executed_today += 1
                
                # Log to journal
                from core.decision_journal import save_signal
                await save_signal(
                    symbol=scan_result.pair,
                    signal="LONG",
                    score=scan_result.score,
                    regime=scan_result.regime,
                    score_breakdown=scan_result.confidence_breakdown,
                    reasons={"source": "autonomous_scanner"},
                    setup_type="SCANNER_SIGNAL"
                )
                
                # Audit log
                from core.audit import log_event
                log_event("INFO", f"Auto-trade executed: {scan_result.pair}", 
                         context=f"Score: {scan_result.score}, Qty: {quantity}")
                
                logger.info(f"AUTO-TRADE: {scan_result.pair} executed @ ${scan_result.entry_price:.4f}, Qty: {quantity}")
                return True
            else:
                logger.warning(f"Trade execution failed: {result.message}")
                return False
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return False
    
    async def _execution_loop(self):
        """Execute trades from scan results."""
        while self._running:
            try:
                # Check if we can trade
                can_trade, reason = await self._can_execute_trade()
                
                if can_trade:
                    # Get top opportunities
                    opportunities = await self.get_top_opportunities(limit=3)
                    
                    for opp in opportunities:
                        # Verify we can still trade
                        can_trade, _ = await self._can_execute_trade()
                        if not can_trade:
                            break
                        
                        # Execute trade
                        await self._execute_trade(opp)
                        
                        # Small delay between trades
                        await asyncio.sleep(5)
                
                # Check daily reset
                now = datetime.utcnow()
                if (now - self._last_execution_reset).days >= 1:
                    self._trades_executed_today = 0
                    self._last_execution_reset = now
                    logger.info("Daily trade counter reset")
                
                # Check every 60 seconds
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Execution loop error: {e}")
                await asyncio.sleep(60)
    
    async def _scan_loop(self):
        """Main scanning loop."""
        while self._running:
            try:
                results = await self.scan_all()
                
                async with self._lock:
                    for result in results:
                        self._scan_cache[result.pair] = result
                
                trade_count = len([r for r in results if r.status == ScanStatus.TRADE])
                if trade_count > 0:
                    logger.info(f"Scanner found {trade_count} trade opportunities")
                
                await asyncio.sleep(self._scan_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan loop error: {e}")
                await asyncio.sleep(60)
    
    async def get_top_opportunities(self, limit: int = 3) -> List[ScanResult]:
        """Get top trading opportunities ranked by score."""
        # Use cached results if available
        cached = [r for r in self._scan_cache.values() if r.status == ScanStatus.TRADE]
        if cached:
            cached.sort(key=lambda x: x.score, reverse=True)
            return cached[:limit]
        
        # Otherwise scan fresh
        results = await self.scan_all()
        trade_signals = [r for r in results if r.status == ScanStatus.TRADE]
        trade_signals.sort(key=lambda x: x.score, reverse=True)
        return trade_signals[:limit]
    
    async def get_why_not(self, pair: str) -> ScanResult:
        """Get detailed rejection analysis for a pair."""
        return await self.scan_pair(pair)
    
    def get_cached_result(self, pair: str) -> Optional[ScanResult]:
        """Get cached scan result for a pair."""
        return self._scan_cache.get(pair)
    
    def get_stats(self) -> dict:
        """Get scanner statistics."""
        return {
            "watchlist_size": len(self._watchlist),
            "total_scans": self.total_scans,
            "trade_signals": self.trade_signals,
            "trades_executed": self.trades_executed,
            "rejections": self.rejections,
            "trades_today": self._trades_executed_today,
            "signal_rate": f"{(self.trade_signals / max(1, self.total_scans) * 100):.1f}%",
            "running": self._running,
            "last_scan": {k: v.isoformat() for k, v in self._last_scan.items()}
        }


# Global instance
_scanner: Optional[MarketScanner] = None


def get_scanner() -> MarketScanner:
    """Get scanner instance."""
    global _scanner
    if _scanner is None:
        _scanner = MarketScanner()
    return _scanner
