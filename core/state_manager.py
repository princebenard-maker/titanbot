"""
state_manager.py - WAVE 2D
Titan System State Manager
Deterministic state transitions.
"""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Titan must always exist in exactly one state."""
    BOOTING = "BOOTING"
    READY = "READY"
    ANALYZING = "ANALYZING"
    PAPER_TRADING = "PAPER_TRADING"
    SAFE_MODE = "SAFE_MODE"
    RECOVERING = "RECOVERING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: SystemState
    to_state: SystemState
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[int] = None


class StateManager:
    """
    Manages Titan's system state.
    All state transitions are explicit and logged.
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        SystemState.BOOTING: {SystemState.READY, SystemState.ERROR, SystemState.SHUTDOWN},
        SystemState.READY: {SystemState.ANALYZING, SystemState.PAPER_TRADING, SystemState.PAUSED, SystemState.ERROR, SystemState.SHUTDOWN},
        SystemState.ANALYZING: {SystemState.READY, SystemState.PAPER_TRADING, SystemState.PAUSED, SystemState.ERROR},
        SystemState.PAPER_TRADING: {SystemState.SAFE_MODE, SystemState.ANALYZING, SystemState.PAUSED, SystemState.ERROR},
        SystemState.SAFE_MODE: {SystemState.PAPER_TRADING, SystemState.RECOVERING, SystemState.PAUSED, SystemState.ERROR},
        SystemState.RECOVERING: {SystemState.READY, SystemState.SAFE_MODE, SystemState.ERROR, SystemState.SHUTDOWN},
        SystemState.PAUSED: {SystemState.READY, SystemState.ERROR, SystemState.SHUTDOWN},
        SystemState.ERROR: {SystemState.RECOVERING, SystemState.SAFE_MODE, SystemState.SHUTDOWN},
        SystemState.SHUTDOWN: {SystemState.BOOTING},
    }
    
    def __init__(self):
        self._state = SystemState.BOOTING
        self._transitions: list[StateTransition] = []
        self._lock = asyncio.Lock()
        self._listeners: list = []
    
    @property
    def state(self) -> SystemState:
        """Current system state."""
        return self._state
    
    async def transition(self, new_state: SystemState, reason: str, user_id: Optional[int] = None) -> bool:
        """
        Attempt state transition.
        Returns True if successful, False if invalid transition.
        """
        async with self._lock:
            if new_state == self._state:
                return True  # Already in state
            
            if new_state not in self.VALID_TRANSITIONS.get(self._state, set()):
                logger.error(f"Invalid transition: {self._state.value} -> {new_state.value}")
                return False
            
            transition = StateTransition(
                from_state=self._state,
                to_state=new_state,
                reason=reason,
                user_id=user_id
            )
            self._transitions.append(transition)
            
            old_state = self._state
            self._state = new_state
            
            logger.info(f"State transition: {old_state.value} -> {new_state.value} | Reason: {reason}")
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    await listener(old_state, new_state, reason)
                except Exception as e:
                    logger.warning(f"State listener error: {e}")
            
            return True
    
    def can_trade(self) -> bool:
        """Check if trading is allowed in current state."""
        return self._state in {
            SystemState.PAPER_TRADING,
            SystemState.ANALYZING,  # Can analyze but not trade
        }
    
    def can_analyze(self) -> bool:
        """Check if analysis is allowed in current state."""
        return self._state not in {
            SystemState.SHUTDOWN,
            SystemState.ERROR,
        }
    
    def is_critical(self) -> bool:
        """Check if system is in critical state."""
        return self._state in {
            SystemState.ERROR,
            SystemState.SHUTDOWN,
        }
    
    def get_transition_history(self, limit: int = 50) -> list[StateTransition]:
        """Get recent state transitions."""
        return self._transitions[-limit:]
    
    def add_listener(self, listener):
        """Add a state change listener."""
        self._listeners.append(listener)
    
    def remove_listener(self, listener):
        """Remove a state change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def get_state_info(self) -> dict:
        """Get current state information."""
        return {
            "state": self._state.value,
            "can_trade": self.can_trade(),
            "can_analyze": self.can_analyze(),
            "is_critical": self.is_critical(),
            "last_transition": self._transitions[-1].__dict__ if self._transitions else None,
            "transition_count": len(self._transitions),
        }


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


async def initialize_state():
    """Initialize state manager and transition to READY."""
    manager = get_state_manager()
    await manager.transition(SystemState.READY, "System initialized")
    return manager


async def shutdown_state():
    """Shutdown state manager."""
    manager = get_state_manager()
    await manager.transition(SystemState.SHUTDOWN, "System shutdown")
