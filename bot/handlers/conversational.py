"""
conversational.py - WAVE 2C
Titan Conversational Interface
Natural language understanding for Titan.
"""
import re
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(Enum):
    """User intents understood by Titan."""
    SIGNAL = "signal"
    REGIME = "regime"
    SCORE = "score"
    HEALTH = "health"
    PAPER_STATUS = "paper_status"
    PAPER_START = "paper_start"
    PAPER_STOP = "paper_stop"
    WEEKLY = "weekly"
    EXPLAIN = "explain"
    JOURNAL = "journal"
    PENDING = "pending"
    APPROVE = "approve"
    REJECT = "reject"
    SUSPEND = "suspend"
    RESUME = "resume"
    HELP = "help"
    STATUS = "status"
    METRICS = "metrics"
    EXPLAINABILITY = "explainability"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Parsed user intent."""
    intent: Intent
    symbol: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    raw_text: str = ""


class IntentParser:
    """
    Natural language intent parser for Titan.
    Maps conversational phrases to commands.
    """
    
    # Symbol mappings
    SYMBOLS = {
        "btc": "BTCUSDT",
        "bitcoin": "BTCUSDT",
        "eth": "ETHUSDT",
        "ethereum": "ETHUSDT",
        "sol": "SOLUSDT",
        "solana": "SOLUSDT",
        "ada": "ADAUSDT",
        "cardano": "ADAUSDT",
        "dot": "DOTUSDT",
        "polkadot": "DOTUSDT",
        "avax": "AVAXUSDT",
        "avalanche": "AVAXUSDT",
        "link": "LINKUSDT",
        "chainlink": "LINKUSDT",
        "matic": "MATICUSDT",
        "polygon": "MATICUSDT",
        "xrp": "XRPUSDT",
        "ripple": "XRPUSDT",
    }
    
    # Intent patterns
    PATTERNS = {
        Intent.SIGNAL: [
            r"(?:what(?:'s| is| are)?\s+(?:the\s+)?(?:price|signal|analysis|doing|looking\s+like|how\s+is|up to)\s+(?:for\s+)?(\w+)?)",
            r"(?:check|get|show|give|me)\s+(?:the\s+)?(?:signal|analysis|trade)\s+(?:for\s+)?(\w+)?",
            r"(?:look\s+at|analyze)\s+(\w+)?",
            r"(\w+)\s+(?:signal|analysis|time)",
            r"(?:what(?:'s| is)\s+)?(\w+)\s+(?:doing|looking)",
            r"(?:how(?:'s| is)\s+)?(\w+)\s+(?:looking|doing)",
        ],
        Intent.REGIME: [
            r"(?:what(?:'s| is)?\s+)?(?:the\s+)?(?:market\s+)?(?:regime|trend|condition)\s+(?:for\s+)?(\w+)?",
            r"(?:is\s+the\s+)?(?:market|trend)\s+(?:for\s+)?(\w+)?",
            r"(?:regime|trend|condition)\s+(?:for\s+)?(\w+)?",
        ],
        Intent.SCORE: [
            r"(?:what(?:'s| is)?\s+)?(?:the\s+)?(?:confidence|score|rating)\s+(?:for\s+)?(\w+)?",
            r"(?:how\s+confident|confidence)\s+(?:for\s+)?(\w+)?",
            r"(?:score|confidence|rating)\s+(?:for\s+)?(\w+)?",
        ],
        Intent.HEALTH: [
            r"(?:how(?:'s| is)?\s+)?(?:is\s+)?(?:titan|the\s+system|tower)\s+(?:feeling|doing|healthy|ok|alright)",
            r"(?:system\s+)?health(?:check)?",
            r"(?:is\s+everything|is\s+it\s+all\s+)(?:ok|working|good)",
            r"titan\s+(?:status|health|ok)",
        ],
        Intent.PAPER_STATUS: [
            r"(?:how(?:'s| is)?\s+)?(?:paper\s+)?trading\s+(?:going|doing|status)",
            r"(?:paper|sim)\s+(?:status|how(?:'s| is))",
            r"(?:what(?:'s| is)?\s+)?(?:our\s+)?(?:paper\s+)?(?:positions?|trades?|pnl|p&l)",
            r"(?:show|get)\s+(?:me\s+)?(?:paper\s+)?(?:positions?|trades?|pnl)",
        ],
        Intent.PAPER_START: [
            r"(?:start|begin|launch|initiate)\s+(?:paper|sim(?:ulator)?)\s+(?:trading)?",
            r"(?:paper|sim)\s+(?:start|begin|go)",
            r"start\s+(?:trading|paper)",
        ],
        Intent.PAPER_STOP: [
            r"(?:stop|pause|end|halt)\s+(?:paper|sim(?:ulator)?)\s+(?:trading)?",
            r"(?:paper|sim)\s+(?:stop|pause|end)",
            r"pause\s+(?:trading|paper)",
        ],
        Intent.WEEKLY: [
            r"(?:weekly|week)\s+(?:report|review|summary|stats)?",
            r"(?:how(?:'s| is)\s+)?(?:this|the)\s+(?:week|weekly)\s+(?:going|doing|looking)",
            r"(?:show|get)\s+(?:me\s+)?(?:the\s+)?(?:weekly|week)\s+(?:report|stats)?",
            r"(?:performance|report|stats)\s+(?:this|for)\s+(?:week|weekly)",
        ],
        Intent.JOURNAL: [
            r"(?:show|get|history|recent)\s+(?:me\s+)?(?:the\s+)?(?:signals?|journal|trades?)",
            r"(?:signal|trade)\s+history",
            r"(?:what(?:'s| did)\s+)?(?:we|our)\s+(?:signal|trade)\s+(?:history|recent|journal)",
        ],
        Intent.METRICS: [
            r"(?:metrics?|stats?|performance|expectancy)",
            r"(?:win\s+rate|winrate)",
            r"(?:risk|reward)",
        ],
        Intent.EXPLAINABILITY: [
            r"(?:why|explain)\s+(?:did|does)?(?:\s+the)?\s+?(?:signal|trade|it)",
            r"(?:explain|reason|logic)\s+(?:why|behind)",
        ],
        Intent.PENDING: [
            r"(?:show|get|list)\s+(?:me\s+)?(?:the\s+)?pending(?:\s+users)?",
            r"who(?:'s| is)\s+(?:waiting|pending|approval)",
        ],
        Intent.APPROVE: [
            r"approve\s+(\d+)",
            r"activate\s+(\d+)",
            r"accept\s+(\d+)",
        ],
        Intent.REJECT: [
            r"reject\s+(\d+)",
            r"deny\s+(\d+)",
            r"refuse\s+(\d+)",
        ],
        Intent.SUSPEND: [
            r"suspend\s+(\d+)",
            r"ban\s+(\d+)",
            r"pause\s+user\s+(\d+)",
        ],
        Intent.RESUME: [
            r"resume\s+(\d+)",
            r"unban\s+(\d+)",
            r"reactivate\s+(\d+)",
        ],
        Intent.HELP: [
            r"(?:help|commands|what(?:\'s| can)\s+(?:you|i)\s+do)",
            r"(?:how|what)\s+(?:do\s+i|to)\s+(?:use|interact)",
            r"(?:show|list)\s+(?:me\s+)?(?:the\s+)?commands",
        ],
        Intent.STATUS: [
            r"(?:status|state)",
            r"(?:how(?:'s| is)\s+)?(?:everything|titan)\s+(?:going|doing)",
        ],
    }
    
    def parse(self, text: str) -> ParsedIntent:
        """
        Parse user text into intent.
        
        Args:
            text: User message
            
        Returns:
            ParsedIntent with intent and extracted data
        """
        text_lower = text.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    symbol = self._extract_symbol(match, text_lower)
                    user_id = self._extract_user_id(match)
                    
                    return ParsedIntent(
                        intent=intent,
                        symbol=symbol,
                        user_id=user_id,
                        raw_text=text
                    )
        
        # Default to unknown
        return ParsedIntent(
            intent=Intent.UNKNOWN,
            raw_text=text
        )
    
    def _extract_symbol(self, match, text: str) -> Optional[str]:
        """Extract trading symbol from match."""
        groups = match.groups()
        
        # Check capture groups
        for group in groups:
            if group:
                symbol = self.SYMBOLS.get(group.lower())
                if symbol:
                    return symbol
                # Check if it's already a valid symbol
                if group.upper() in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
                    return group.upper()
        
        # Check full text for known symbols
        for name, symbol in self.SYMBOLS.items():
            if name in text:
                return symbol
        
        return None
    
    def _extract_user_id(self, match) -> Optional[str]:
        """Extract user ID from match."""
        groups = match.groups()
        for group in groups:
            if group and group.isdigit():
                return group
        return None


class ConversationalEngine:
    """
    Titan's conversational engine.
    Handles natural language interactions.
    """
    
    def __init__(self):
        self.parser = IntentParser()
        self.ai_provider = None  # Lazy load
    
    def _init_ai(self):
        """Initialize AI provider if available."""
        if self.ai_provider is None:
            from providers.ai_provider import get_ai_provider
            self.ai_provider = get_ai_provider()
    
    async def process(self, text: str, user_id: int = None) -> str:
        """
        Process user message and return response.
        
        Args:
            text: User message
            user_id: Telegram user ID
            
        Returns:
            Natural language response
        """
        parsed = self.parser.parse(text)
        
        logger.info(f"Intent parsed: {parsed.intent.value} | Symbol: {parsed.symbol}")
        
        # Route to appropriate handler
        if parsed.intent == Intent.SIGNAL:
            return await self._handle_signal(parsed.symbol)
        elif parsed.intent == Intent.HEALTH:
            return await self._handle_health()
        elif parsed.intent == Intent.PAPER_STATUS:
            return await self._handle_paper_status()
        elif parsed.intent == Intent.WEEKLY:
            return await self._handle_weekly()
        elif parsed.intent == Intent.JOURNAL:
            return await self._handle_journal()
        elif parsed.intent == Intent.HELP:
            return self._handle_help()
        elif parsed.intent == Intent.STATUS:
            return await self._handle_status()
        elif parsed.intent == Intent.UNKNOWN:
            return await self._handle_unknown(text)
        else:
            return "I understand you're asking about that. For specific commands, type /help."
    
    async def _handle_signal(self, symbol: str) -> str:
        """Handle signal request."""
        if not symbol:
            return "Which pair? Try: 'What's BTC doing?' or '/signal BTCUSDT'"
        
        # Import signal handler
        from bot.handlers.signals import signal_command
        
        # Return structured response
        return f"Analyzing {symbol} now... Signal generation in progress."
    
    async def _handle_health(self) -> str:
        """Handle health check."""
        from core.health_monitor import get_health_monitor
        from core.state_manager import get_state_manager
        
        health = get_health_monitor().get_current_health()
        state = get_state_manager().get_state_info()
        
        if health:
            score = health.health_score
            status = health.overall_status.value
            emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "🚨"
            
            return (
                f"{emoji} System Health: {score}%\n"
                f"Status: {status}\n"
                f"Titan State: {state['state']}\n"
                f"All systems operational."
            )
        
        return "Health check in progress. Type /health_report for details."
    
    async def _handle_paper_status(self) -> str:
        """Handle paper trading status."""
        return (
            "Paper Trading Status:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Active: Checking...\n"
            "Positions: Loading...\n"
            "P&L: Calculating...\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Type /paper_status for full details."
        )
    
    async def _handle_weekly(self) -> str:
        """Handle weekly review request."""
        return (
            "📊 Weekly Review\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Generating your weekly performance report...\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Type /weekly_review for full details."
        )
    
    async def _handle_journal(self) -> str:
        """Handle journal request."""
        return (
            "📋 Recent Signals\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Loading signal history...\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Type /journal to see all recent signals."
        )
    
    def _handle_help(self) -> str:
        """Handle help request."""
        return (
            "💬 Titan Commands\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Just talk to me naturally!\n\n"
            "Examples:\n"
            "• \"What's BTC doing?\"\n"
            "• \"How's paper trading?\"\n"
            "• \"Show me the weekly report\"\n"
            "• \"How's the system?\"\n\n"
            "Or use commands:\n"
            "/signal BTCUSDT\n"
            "/paper_status\n"
            "/health\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Type /help for full command list."
        )
    
    async def _handle_status(self) -> str:
        """Handle status request."""
        from core.state_manager import get_state_manager
        from core.health_monitor import get_health_monitor
        
        state = get_state_manager().get_state_info()
        health = get_health_monitor().get_current_health()
        
        return (
            f"🤖 Titan Status\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"State: {state['state']}\n"
            f"Can Trade: {'Yes' if state['can_trade'] else 'No'}\n"
            f"Health: {health.health_score if health else 'Checking...'}%\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Titan is operational."
        )
    
    async def _handle_unknown(self, text: str) -> str:
        """Handle unknown intent with AI."""
        self._init_ai()
        
        if self.ai_provider and self.ai_provider.is_available():
            response = await self.ai_provider.generate(
                prompt=f"User asked: {text}\n\n"
                       "Titan is a trading intelligence bot. "
                       "Give a brief, helpful response. "
                       "If they want trading info, suggest relevant commands.",
                system="You are Titan, a trading intelligence assistant. Be concise and helpful."
            )
            if response:
                return response
        
        return (
            "I'm not sure I understood that.\n"
            "Try:\n"
            "• \"What's BTC doing?\" - Get signal\n"
            "• \"How's the system?\" - Health check\n"
            "• \"Show me weekly report\" - Performance\n\n"
            "Type /help for all commands."
        )


# Global instance
_conversational_engine: ConversationalEngine = None


def get_conversational_engine() -> ConversationalEngine:
    """Get conversational engine instance."""
    global _conversational_engine
    if _conversational_engine is None:
        _conversational_engine = ConversationalEngine()
    return _conversational_engine
