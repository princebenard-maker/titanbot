"""
ai_provider.py - WAVE 3C
Titan AI Provider - OpenRouter Integration
Free LLM models for conversational interface.
"""
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AIProvider:
    """Abstract AI provider interface."""
    
    @property
    def name(self) -> str:
        return "base"
    
    def is_available(self) -> bool:
        return False
    
    async def generate(self, prompt: str, system: str = None, max_tokens: int = 500) -> str:
        return "AI not configured"


class OpenRouterProvider(AIProvider):
    """
    OpenRouter AI provider.
    Free tier models:
    - google/gemini-2.0-flash-thinking-exp-01-21
    - anthropic/claude-3-haiku
    - openai/gpt-4o-mini
    - minimax/minimax-ai-report (if available)
    - NVIDIA/llama-3.1-nemotron-70b-instruct (free)
    """
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Free models in priority order
    FREE_MODELS = [
        "google/gemini-2.0-flash-thinking-exp-01-21",  # Best free thinking model
        "anthropic/claude-3-haiku",  # Fast, capable
        "nvidia/llama-3.1-nemotron-70b-instruct",  # Strong but larger
        "openai/gpt-4o-mini",  # Fast and capable
    ]
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-thinking-exp-01-21")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "https://github.com/princebenard-maker/titanbot")
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "TitanBot")
    
    @property
    def name(self) -> str:
        return "OpenRouter"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, system: str = None, max_tokens: int = 800) -> Optional[str]:
        """
        Generate response using OpenRouter API.
        
        Args:
            prompt: User prompt
            system: System instruction
            max_tokens: Max response length
            
        Returns:
            AI response string or None on error
        """
        import aiohttp
        
        if not self.api_key:
            logger.warning("OpenRouter API key not set")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter error {response.status}: {error_text}")
                        return None
                    
                    data = await response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("OpenRouter timeout")
            return None
        except Exception as e:
            logger.error(f"OpenRouter exception: {e}")
            return None
    
    async def generate_trading_signal(self, signal_data: dict) -> str:
        """
        Generate natural language signal explanation.
        
        Args:
            signal_data: Signal details
            
        Returns:
            Human-readable signal explanation
        """
        system_prompt = """You are Titan, a trading intelligence assistant. 
Provide clear, concise signal explanations. Include:
- Entry price
- Stop loss
- Take profit
- Risk:reward ratio
- Brief rationale

Format as Telegram message with emojis."""
        
        prompt = f"""Analyze this trading signal:

Symbol: {signal_data.get('pair', 'N/A')}
Direction: {signal_data.get('side', 'N/A')}
Entry: ${signal_data.get('entry', 0):,.2f}
Stop Loss: ${signal_data.get('stop_loss', 0):,.2f}
Take Profit: ${signal_data.get('take_profit', 0):,.2f}
Score: {signal_data.get('score', 0)}/40
Regime: {signal_data.get('regime', 'N/A')}
Setup: {signal_data.get('setup', 'N/A')}
ATR: {signal_data.get('atr', 0):.2f}%

Provide a brief, actionable explanation."""
        
        return await self.generate(prompt, system_prompt)


class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""
    
    @property
    def name(self) -> str:
        return "MockAI"
    
    def is_available(self) -> bool:
        return True
    
    async def generate(self, prompt: str, system: str = None, max_tokens: int = 500) -> str:
        prompt_lower = prompt.lower()
        
        if "signal" in prompt_lower or "btc" in prompt_lower:
            return "📊 BTCUSDT Analysis\n\nSignal: LONG\nConfidence: High\n\nEntry: $67,200\nStop: $66,600\nTarget: $68,500\n\nR:R = 1:2.1"
        elif "eth" in prompt_lower:
            return "📊 ETHUSDT Analysis\n\nSignal: WAIT\nConfidence: Medium\n\nConsolidating. Waiting for breakout."
        elif "health" in prompt_lower:
            return "✅ System Health: 95%\n\nAll subsystems operational."
        elif "paper" in prompt_lower or "account" in prompt_lower:
            return "📈 Paper Account\n\nBalance: $10.00\nTrades: 0\nWin Rate: N/A"
        else:
            return "Understood. Processing your request."


# Provider instances
_openrouter_provider: Optional[OpenRouterProvider] = None
_mock_provider: Optional[MockAIProvider] = None


def get_ai_provider() -> AIProvider:
    """Get AI provider based on available credentials."""
    global _openrouter_provider, _mock_provider
    
    if _openrouter_provider is None:
        _openrouter_provider = OpenRouterProvider()
    
    if _openrouter_provider.is_available():
        return _openrouter_provider
    
    if _mock_provider is None:
        _mock_provider = MockAIProvider()
    
    return _mock_provider


def is_ai_available() -> bool:
    """Check if AI provider is available."""
    return get_ai_provider().is_available()


async def explain_signal(signal_data: dict) -> str:
    """Get AI explanation for a signal."""
    provider = get_ai_provider()
    
    if isinstance(provider, OpenRouterProvider):
        return await provider.generate_trading_signal(signal_data)
    
    # Mock response
    return f"""📊 {signal_data.get('pair', 'N/A')} Signal

Direction: {signal_data.get('side', 'N/A')}
Entry: ${signal_data.get('entry', 0):,.2f}
Stop: ${signal_data.get('stop_loss', 0):,.2f}
Target: ${signal_data.get('take_profit', 0):,.2f}

Confidence: {signal_data.get('score', 0)}/40
Regime: {signal_data.get('regime', 'N/A')}
Setup: {signal_data.get('setup', 'N/A')}"""
