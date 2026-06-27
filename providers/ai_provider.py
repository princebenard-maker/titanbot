"""
ai_provider.py - WAVE 2C
Titan AI Provider Abstraction
Supports OpenRouter and future providers.
"""
import os
import asyncio
import logging

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
    Free tier available with various models.
    """
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    @property
    def name(self) -> str:
        return "OpenRouter"
    
    def is_available(self) -> bool:
        return bool(os.getenv("OPENROUTER_API_KEY"))
    
    async def generate(self, prompt: str, system: str = None, max_tokens: int = 500) -> str:
        import aiohttp
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None
        
        model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-thinking-exp-01-21")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
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
                        error = await response.text()
                        logger.error(f"OpenRouter error: {response.status}")
                        return None
                    
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                    
        except asyncio.TimeoutError:
            logger.error("OpenRouter timeout")
            return None
        except Exception as e:
            logger.error(f"OpenRouter exception: {e}")
            return None


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
            return "BTCUSDT showing strength. Long signal with high confidence."
        elif "eth" in prompt_lower:
            return "ETHUSD consolidating. Wait for breakout confirmation."
        elif "health" in prompt_lower:
            return "System health stable. All subsystems operational."
        elif "paper" in prompt_lower:
            return "Paper trading status nominal. Monitoring positions."
        else:
            return "Understood. Processing your request."


def get_ai_provider() -> AIProvider:
    """Get AI provider based on available credentials."""
    if os.getenv("OPENROUTER_API_KEY"):
        return OpenRouterProvider()
    return MockAIProvider()


def is_ai_available() -> bool:
    """Check if AI provider is available."""
    return get_ai_provider().is_available()
