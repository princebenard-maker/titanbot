"""
exchange.py - WAVE 3A
Exchange Utilities
Provides unified market data access.
"""
import logging
import ccxt
from typing import Optional

logger = logging.getLogger(__name__)

# Exchange instance
_exchange = None


def get_exchange():
    """Get CCXT exchange instance."""
    global _exchange
    
    if _exchange is None:
        # Get data source from environment
        import os
        data_source = os.getenv("DATA_SOURCE", "kraken")
        
        _exchange = ccxt.kraken({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })
        
        logger.info(f"Exchange initialized: {data_source}")
    
    return _exchange


async def get_market_price(pair: str) -> float:
    """
    Get current market price for pair.
    
    Args:
        pair: Trading pair (e.g., BTCUSDT)
        
    Returns:
        Current price
    """
    try:
        exchange = get_exchange()
        
        # Normalize pair for CCXT
        symbol = pair.replace('USDT', '/USDT') if 'USDT' in pair else pair
        if '/' not in symbol:
            symbol = symbol + '/USDT'
        
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
        
    except Exception as e:
        logger.error(f"Failed to get price for {pair}: {e}")
        return 0.0


async def fetch_ohlcv(pair: str, timeframe: str = '1h', limit: int = 100):
    """
    Fetch OHLCV candles.
    
    Args:
        pair: Trading pair
        timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles
        
    Returns:
        List of candles [[timestamp, open, high, low, close, volume], ...]
    """
    try:
        exchange = get_exchange()
        
        # Normalize pair
        symbol = pair.replace('USDT', '/USDT') if 'USDT' in pair else pair
        if '/' not in symbol:
            symbol = symbol + '/USDT'
        
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return candles
        
    except Exception as e:
        logger.error(f"Failed to fetch candles for {pair}: {e}")
        return []
