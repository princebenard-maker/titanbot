"""
health_monitor.py - WAVE 2D
Titan Health Monitor
Verifies all subsystems every 5 minutes.
"""
import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class SubsystemHealth:
    """Health status of a single subsystem."""
    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    consecutive_failures: int = 0


@dataclass
class SystemHealth:
    """Overall system health."""
    overall_status: HealthStatus
    health_score: int  # 0-100
    subsystems: dict[str, SubsystemHealth]
    last_full_check: datetime
    check_duration_ms: float


class HealthMonitor:
    """
    Monitors all Titan subsystems.
    Runs checks every 5 minutes.
    """
    
    CHECK_INTERVAL = 300  # 5 minutes
    
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._subsystems: dict[str, SubsystemHealth] = {}
        self._lock = asyncio.Lock()
        self._last_full_health: Optional[SystemHealth] = None
        
    async def start(self):
        """Start the health monitor."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started")
    
    async def stop(self):
        """Stop the health monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self.run_full_check()
                await asyncio.sleep(self.CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)  # Retry after 1 min on error
    
    async def run_full_check(self) -> SystemHealth:
        """Run all health checks."""
        start_time = datetime.utcnow()
        
        checks = [
            self._check_database(),
            self._check_disk_space(),
            self._check_memory(),
            self._check_titan_state(),
            self._check_journal(),
            self._check_config(),
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        async with self._lock:
            for result in results:
                if isinstance(result, Exception):
                    continue
                if isinstance(result, SubsystemHealth):
                    self._subsystems[result.name] = result
            
            # Calculate overall health
            overall, score = self._calculate_overall_health()
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._last_full_health = SystemHealth(
                overall_status=overall,
                health_score=score,
                subsystems=self._subsystems.copy(),
                last_full_check=datetime.utcnow(),
                check_duration_ms=duration
            )
            
            # Log health status
            if overall == HealthStatus.CRITICAL:
                logger.critical(f"System health: {overall.value} ({score}%)")
            elif overall == HealthStatus.WARNING:
                logger.warning(f"System health: {overall.value} ({score}%)")
            else:
                logger.info(f"System health: {overall.value} ({score}%)")
        
        return self._last_full_health
    
    async def _check_database(self) -> SubsystemHealth:
        """Check database connectivity and integrity."""
        import time
        start = time.time()
        
        try:
            db_path = os.getenv("DB_PATH", "./data/titanbot.db")
            
            if not os.path.exists(db_path):
                return SubsystemHealth(
                    name="database",
                    status=HealthStatus.CRITICAL,
                    message="Database file not found"
                )
            
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            
            # Check if we can read
            cursor.execute("SELECT COUNT(*) FROM signals")
            cursor.execute("SELECT COUNT(*) FROM users")
            
            conn.close()
            
            response_time = (time.time() - start) * 1000
            
            return SubsystemHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database accessible",
                response_time_ms=response_time
            )
        except sqlite3.OperationalError as e:
            return SubsystemHealth(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}"
            )
        except Exception as e:
            return SubsystemHealth(
                name="database",
                status=HealthStatus.WARNING,
                message=f"Database check failed: {str(e)}"
            )
    
    async def _check_disk_space(self) -> SubsystemHealth:
        """Check available disk space."""
        try:
            stat = os.statvfs(".")
            free_percent = (stat.f_bavail / stat.f_blocks) * 100
            
            if free_percent < 10:
                return SubsystemHealth(
                    name="disk_space",
                    status=HealthStatus.CRITICAL,
                    message=f"Low disk space: {free_percent:.1f}%"
                )
            elif free_percent < 20:
                return SubsystemHealth(
                    name="disk_space",
                    status=HealthStatus.WARNING,
                    message=f"Disk space warning: {free_percent:.1f}%"
                )
            
            return SubsystemHealth(
                name="disk_space",
                status=HealthStatus.HEALTHY,
                message=f"Disk space OK: {free_percent:.1f}%"
            )
        except Exception as e:
            return SubsystemHealth(
                name="disk_space",
                status=HealthStatus.WARNING,
                message=f"Disk check failed: {str(e)}"
            )
    
    async def _check_memory(self) -> SubsystemHealth:
        """Check memory usage."""
        try:
            # Simple memory check using /proc on Linux
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = parts[1].strip()
            
            if "MemAvailable" in mem_info and "MemTotal" in mem_info:
                available = int(mem_info["MemAvailable"].split()[0])
                total = int(mem_info["MemTotal"].split()[0])
                used_percent = ((total - available) / total) * 100
                
                if used_percent > 90:
                    return SubsystemHealth(
                        name="memory",
                        status=HealthStatus.CRITICAL,
                        message=f"Memory critical: {used_percent:.1f}% used"
                    )
                elif used_percent > 80:
                    return SubsystemHealth(
                        name="memory",
                        status=HealthStatus.WARNING,
                        message=f"Memory warning: {used_percent:.1f}% used"
                    )
                
                return SubsystemHealth(
                    name="memory",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory OK: {used_percent:.1f}% used"
                )
            
            return SubsystemHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message="Could not determine memory status"
            )
        except Exception as e:
            return SubsystemHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Memory check failed: {str(e)}"
            )
    
    async def _check_titan_state(self) -> SubsystemHealth:
        """Check Titan's internal state."""
        try:
            from core.state_manager import get_state_manager
            manager = get_state_manager()
            state = manager.state
            
            if state.value in ["ERROR", "SHUTDOWN"]:
                return SubsystemHealth(
                    name="titan_state",
                    status=HealthStatus.CRITICAL,
                    message=f"Titan in critical state: {state.value}"
                )
            elif state.value in ["SAFE_MODE", "RECOVERING"]:
                return SubsystemHealth(
                    name="titan_state",
                    status=HealthStatus.WARNING,
                    message=f"Titan in degraded state: {state.value}"
                )
            
            return SubsystemHealth(
                name="titan_state",
                status=HealthStatus.HEALTHY,
                message=f"Titan state: {state.value}"
            )
        except Exception as e:
            return SubsystemHealth(
                name="titan_state",
                status=HealthStatus.WARNING,
                message=f"State check failed: {str(e)}"
            )
    
    async def _check_journal(self) -> SubsystemHealth:
        """Check journal functionality."""
        try:
            from core.decision_journal import get_recent_signals
            signals = await get_recent_signals(limit=1)
            
            return SubsystemHealth(
                name="journal",
                status=HealthStatus.HEALTHY,
                message=f"Journal accessible, last signal: {signals[0]['timestamp'] if signals else 'None'}"
            )
        except Exception as e:
            return SubsystemHealth(
                name="journal",
                status=HealthStatus.WARNING,
                message=f"Journal check failed: {str(e)}"
            )
    
    async def _check_config(self) -> SubsystemHealth:
        """Check configuration."""
        try:
            from config.settings import ADMIN_PIN_HASH
            from config.constants import ADMIN_TELEGRAM_ID
            
            if not ADMIN_PIN_HASH or ADMIN_TELEGRAM_ID is None:
                return SubsystemHealth(
                    name="config",
                    status=HealthStatus.CRITICAL,
                    message="Critical config missing"
                )
            
            return SubsystemHealth(
                name="config",
                status=HealthStatus.HEALTHY,
                message="Configuration OK"
            )
        except Exception as e:
            return SubsystemHealth(
                name="config",
                status=HealthStatus.WARNING,
                message=f"Config check failed: {str(e)}"
            )
    
    def _calculate_overall_health(self) -> tuple[HealthStatus, int]:
        """Calculate overall health from subsystem statuses."""
        if not self._subsystems:
            return HealthStatus.UNKNOWN, 0
        
        # Weight each subsystem
        weights = {
            "database": 25,
            "titan_state": 20,
            "journal": 15,
            "memory": 15,
            "disk_space": 15,
            "config": 10,
        }
        
        score = 0
        total_weight = 0
        
        critical_count = 0
        warning_count = 0
        
        for name, health in self._subsystems.items():
            weight = weights.get(name, 10)
            total_weight += weight
            
            if health.status == HealthStatus.CRITICAL:
                score += 0
                critical_count += 1
            elif health.status == HealthStatus.WARNING:
                score += weight * 0.5
                warning_count += 1
            else:
                score += weight
        
        if total_weight > 0:
            percentage = int((score / total_weight) * 100)
        else:
            percentage = 0
        
        # Determine status
        if critical_count > 0:
            overall = HealthStatus.CRITICAL
        elif warning_count >= 3:
            overall = HealthStatus.WARNING
        elif warning_count > 0:
            overall = HealthStatus.WARNING if percentage < 80 else HealthStatus.HEALTHY
        else:
            overall = HealthStatus.HEALTHY
        
        return overall, percentage
    
    def get_current_health(self) -> Optional[SystemHealth]:
        """Get last health check result."""
        return self._last_full_health
    
    def get_subsystem_health(self, name: str) -> Optional[SubsystemHealth]:
        """Get specific subsystem health."""
        return self._subsystems.get(name)


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
