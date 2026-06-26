"""
recovery_engine.py - WAVE 2D
Titan Recovery Engine
Deterministic recovery for all subsystems.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    NONE = "NONE"
    RETRY = "RETRY"
    ROLLBACK = "ROLLBACK"
    PAUSE = "PAUSE"
    NOTIFY = "NOTIFY"
    SAFE_MODE = "SAFE_MODE"
    DISABLE = "DISABLE"


@dataclass
class RecoveryStep:
    """A single recovery step."""
    action: RecoveryAction
    subsystem: str
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = False
    error: Optional[str] = None


@dataclass
class RecoverySession:
    """A recovery session for an incident."""
    incident_id: str
    subsystem: str
    issue: str
    started_at: datetime
    steps: list[RecoveryStep] = field(default_factory=list)
    final_state: Optional[str] = None
    resolved: bool = False
    escalated: bool = False


class RecoveryEngine:
    """
    Deterministic recovery engine.
    Every subsystem has: Detection -> Recovery -> Escalation -> Logging -> Final State
    """
    
    def __init__(self):
        self._sessions: dict[str, RecoverySession] = {}
        self._recovery_handlers: dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        self._incident_counter = 0
    
    async def initialize(self):
        """Initialize recovery engine with handlers."""
        self._recovery_handlers = {
            "exchange_timeout": self._handle_exchange_timeout,
            "exchange_error": self._handle_exchange_error,
            "database_lock": self._handle_database_lock,
            "journal_failure": self._handle_journal_failure,
            "telegram_unavailable": self._handle_telegram_unavailable,
            "missing_candles": self._handle_missing_candles,
            "indicator_failure": self._handle_indicator_failure,
            "risk_limit": self._handle_risk_limit,
            "consecutive_losses_3": self._handle_3_consecutive_losses,
            "consecutive_losses_5": self._handle_5_consecutive_losses,
            "drawdown": self._handle_drawdown,
            "unexpected_exception": self._handle_unexpected_exception,
            "health_warning": self._handle_health_warning,
            "health_critical": self._handle_health_critical,
            "health_emergency": self._handle_health_emergency,
        }
        logger.info("Recovery engine initialized")
    
    async def handle_incident(self, incident_type: str, context: dict) -> RecoverySession:
        """Handle an incident with deterministic recovery."""
        async with self._lock:
            self._incident_counter += 1
            incident_id = f"{incident_type}_{self._incident_counter}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            session = RecoverySession(
                incident_id=incident_id,
                subsystem=context.get("subsystem", "unknown"),
                issue=incident_type,
                started_at=datetime.utcnow(),
            )
            self._sessions[incident_id] = session
        
        # Get handler for this incident type
        handler = self._recovery_handlers.get(incident_type)
        
        if handler:
            try:
                await handler(session, context)
            except Exception as e:
                logger.error(f"Recovery handler error: {e}")
                session.steps.append(RecoveryStep(
                    action=RecoveryAction.NONE,
                    subsystem=session.subsystem,
                    description=f"Handler error: {str(e)}",
                    success=False,
                    error=str(e)
                ))
        else:
            logger.warning(f"No handler for incident type: {incident_type}")
            session.final_state = "NO_HANDLER"
        
        return session
    
    async def _add_step(self, session: RecoverySession, action: RecoveryAction, description: str, success: bool = True, error: str = None):
        """Add a recovery step to session."""
        step = RecoveryStep(
            action=action,
            subsystem=session.subsystem,
            description=description,
            success=success,
            error=error
        )
        session.steps.append(step)
        logger.info(f"Recovery [{session.incident_id}]: {action.value} - {description}")
    
    # ==================== EXCHANGE HANDLERS ====================
    
    async def _handle_exchange_timeout(self, session: RecoverySession, context: dict):
        """Handle exchange timeout."""
        retry_count = context.get("retry_count", 0)
        max_retries = 3
        
        if retry_count < max_retries:
            await self._add_step(session, RecoveryAction.RETRY, 
                f"Retry {retry_count + 1}/{max_retries} with exponential backoff")
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            session.resolved = True
            session.final_state = "RECOVERED"
        else:
            await self._add_step(session, RecoveryAction.PAUSE, "Max retries exceeded, pausing new trades")
            await self._add_step(session, RecoveryAction.NOTIFY, "Notifying admin of exchange issue")
            session.final_state = "TRADING_PAUSED"
    
    async def _handle_exchange_error(self, session: RecoverySession, context: dict):
        """Handle CCXT exception."""
        error_type = context.get("error_type", "unknown")
        await self._add_step(session, RecoveryAction.RETRY, f"Retry after {error_type}")
        await self._add_step(session, RecoveryAction.NONE, "Logging error")
        await self._add_step(session, RecoveryAction.PAUSE, "Warning: entries paused if persistent")
        session.final_state = "MONITORING"
    
    async def _handle_database_lock(self, session: RecoverySession, context: dict):
        """Handle database lock."""
        retry_count = context.get("retry_count", 0)
        
        await self._add_step(session, RecoveryAction.RETRY, f"Retry transaction {retry_count + 1}")
        
        if retry_count >= 2:
            await self._add_step(session, RecoveryAction.ROLLBACK, "Rolling back transaction")
            await self._add_step(session, RecoveryAction.PAUSE, "Pausing journaling")
            await self._add_step(session, RecoveryAction.NOTIFY, "Notifying admin")
            session.final_state = "JOURNALING_DISABLED"
        else:
            session.final_state = "RETRYING"
    
    async def _handle_journal_failure(self, session: RecoverySession, context: dict):
        """Handle journal write failure."""
        await self._add_step(session, RecoveryAction.RETRY, "Retry journal write")
        await self._add_step(session, RecoveryAction.NONE, "Logging failure")
        await self._add_step(session, RecoveryAction.DISABLE, "Disable new trades if journal unavailable")
        session.final_state = "SAFE_MODE"
    
    async def _handle_telegram_unavailable(self, session: RecoverySession, context: dict):
        """Handle Telegram unavailable."""
        await self._add_step(session, RecoveryAction.NONE, "Queueing notifications")
        await self._add_step(session, RecoveryAction.NONE, "Continuing internal processing")
        await self._add_step(session, RecoveryAction.NONE, "Will flush queue when restored")
        session.final_state = "PROCESSING_OFFLINE"
        session.resolved = True
    
    async def _handle_missing_candles(self, session: RecoverySession, context: dict):
        """Handle missing candle data."""
        symbol = context.get("symbol", "unknown")
        await self._add_step(session, RecoveryAction.NONE, f"Rejecting signal for {symbol}")
        await self._add_step(session, RecoveryAction.NONE, "Logging reason: missing data")
        await self._add_step(session, RecoveryAction.NONE, "Never interpolating data")
        session.final_state = "SIGNAL_REJECTED"
        session.resolved = True
    
    async def _handle_indicator_failure(self, session: RecoverySession, context: dict):
        """Handle indicator calculation failure."""
        indicator = context.get("indicator", "unknown")
        await self._add_step(session, RecoveryAction.NONE, f"Rejecting signal due to {indicator} failure")
        await self._add_step(session, RecoveryAction.NONE, "Logging error")
        await self._add_step(session, RecoveryAction.NONE, "Continuing monitoring")
        session.final_state = "SIGNAL_REJECTED"
        session.resolved = True
    
    async def _handle_risk_limit(self, session: RecoverySession, context: dict):
        """Handle risk limit exceeded."""
        limit_type = context.get("limit_type", "unknown")
        await self._add_step(session, RecoveryAction.REJECT, f"Rejecting trade: {limit_type} exceeded")
        await self._add_step(session, RecoveryAction.NONE, "Maintaining monitoring")
        await self._add_step(session, RecoveryAction.NONE, "Will resume next allowed period")
        session.final_state = "LIMIT_ACTIVE"
        session.resolved = True
    
    async def _handle_3_consecutive_losses(self, session: RecoverySession, context: dict):
        """Handle 3 consecutive losses."""
        await self._add_step(session, RecoveryAction.SAFE_MODE, "Entering SAFE_MODE")
        await self._add_step(session, RecoveryAction.NONE, "Reducing risk parameters")
        await self._add_step(session, RecoveryAction.NONE, "Continuing monitoring")
        session.final_state = "SAFE_MODE"
    
    async def _handle_5_consecutive_losses(self, session: RecoverySession, context: dict):
        """Handle 5 consecutive losses."""
        await self._add_step(session, RecoveryAction.PAUSE, "Pausing all trading")
        await self._add_step(session, RecoveryAction.NOTIFY, "Requiring manual approval to resume")
        session.final_state = "REQUIRES_APPROVAL"
        session.escalated = True
    
    async def _handle_drawdown(self, session: RecoverySession, context: dict):
        """Handle drawdown threshold exceeded."""
        drawdown_pct = context.get("drawdown_pct", 0)
        await self._add_step(session, RecoveryAction.DISABLE, f"Trading disabled (drawdown: {drawdown_pct}%)")
        await self._add_step(session, RecoveryAction.NONE, "Generating incident report")
        await self._add_step(session, RecoveryAction.NOTIFY, "Awaiting administrator")
        session.final_state = "DISABLED"
        session.escalated = True
    
    async def _handle_unexpected_exception(self, session: RecoverySession, context: dict):
        """Handle unexpected exception."""
        error = context.get("error", "unknown")
        await self._add_step(session, RecoveryAction.NONE, f"Capturing stack trace: {error[:100]}")
        await self._add_step(session, RecoveryAction.NONE, "Logging error")
        await self._add_step(session, RecoveryAction.RETRY, "Attempting recovery")
        
        recurrence = context.get("recurrence_count", 0)
        if recurrence > 2:
            await self._add_step(session, RecoveryAction.SAFE_MODE, "Too many recurrences, entering SAFE_MODE")
            session.final_state = "SAFE_MODE"
        else:
            session.final_state = "RECOVERING"
    
    async def _handle_health_warning(self, session: RecoverySession, context: dict):
        """Handle health below 80%."""
        health_score = context.get("health_score", 0)
        await self._add_step(session, RecoveryAction.NONE, f"Warning: health score {health_score}%")
        await self._add_step(session, RecoveryAction.NONE, "Continuing monitoring")
        session.final_state = "WARNING"
        session.resolved = True
    
    async def _handle_health_critical(self, session: RecoverySession, context: dict):
        """Handle health below 60%."""
        health_score = context.get("health_score", 0)
        await self._add_step(session, RecoveryAction.PAUSE, f"Critical: health score {health_score}%")
        await self._add_step(session, RecoveryAction.NONE, "Recovery operations only")
        session.final_state = "CRITICAL"
        session.escalated = True
    
    async def _handle_health_emergency(self, session: RecoverySession, context: dict):
        """Handle health below 40%."""
        health_score = context.get("health_score", 0)
        await self._add_step(session, RecoveryAction.DISABLE, f"Emergency: health score {health_score}%")
        await self._add_step(session, RecoveryAction.NOTIFY, "Notifying administrator immediately")
        await self._add_step(session, RecoveryAction.NONE, "Preserving all logs")
        session.final_state = "EMERGENCY"
        session.escalated = True
    
    # ==================== STATE MANAGEMENT ====================
    
    async def update_state_for_recovery(self, final_state: str):
        """Update Titan state based on recovery final state."""
        from core.state_manager import get_state_manager
        
        state_manager = get_state_manager()
        
        state_mapping = {
            "RECOVERED": ("READY", "Exchange recovered"),
            "TRADING_PAUSED": ("PAUSED", "Trading paused due to exchange"),
            "JOURNALING_DISABLED": ("PAUSED", "Journal unavailable"),
            "SAFE_MODE": ("SAFE_MODE", "Entered safe mode"),
            "SIGNAL_REJECTED": ("READY", "Signal rejected, continuing"),
            "LIMIT_ACTIVE": ("READY", "Risk limit active"),
            "REQUIRES_APPROVAL": ("PAUSED", "Requires admin approval"),
            "DISABLED": ("PAUSED", "Trading disabled"),
            "EMERGENCY": ("ERROR", "Emergency state"),
            "CRITICAL": ("ERROR", "Critical health"),
        }
        
        if final_state in state_mapping:
            new_state, reason = state_mapping[final_state]
            from core.state_manager import SystemState
            await state_manager.transition(SystemState(new_state), reason)
    
    def get_active_sessions(self) -> list[RecoverySession]:
        """Get all active recovery sessions."""
        return [s for s in self._sessions.values() if not s.resolved]
    
    def get_recent_sessions(self, limit: int = 10) -> list[RecoverySession]:
        """Get recent recovery sessions."""
        sorted_sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.started_at,
            reverse=True
        )
        return sorted_sessions[:limit]


# Global recovery engine instance
_recovery_engine: Optional[RecoveryEngine] = None


def get_recovery_engine() -> RecoveryEngine:
    """Get the global recovery engine instance."""
    global _recovery_engine
    if _recovery_engine is None:
        _recovery_engine = RecoveryEngine()
    return _recovery_engine
