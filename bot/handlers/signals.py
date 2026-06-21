"""
signals.py - TITAN Wave 2A
Telegram handler for signal monitoring.
Receives signals from Alpha TrendFlow.
No trades executed. Read-only.
"""
import logging
from telegram.ext import Application

logger = logging.getLogger(__name__)

def register_signals(application: Application) -> None:
    """
    Register signal handlers with the Telegram application.
    Placeholder for Wave 2B command integration.
    """
    logger.info("Signal handlers registered")
    pass
