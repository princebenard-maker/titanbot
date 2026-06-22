"""
market_fetcher.py - TITAN Wave 2A
Fetches OHLCV market data from Binance.
READ ONLY. No trading. No orders.
"""
import ccxt
import pandas as pd
import logging
import asyncio

logger = logging.getLogger(__name__)

EXCHANGE = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

SUPPORTED_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT',
    'SOL/USDT', 'ADA/USDT', 'XRP/USDT'
]

async def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: EXCHANGE.fetch_ohlcv(symbol, timeframe, limit=limit)
        )
        df = pd.DataFrame(raw, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        logger.error(f"Failed to fetch {symbol} {timeframe}: {e}")
        return pd.DataFrame()

def is_supported(symbol: str) -> bool:
    normalized = symbol.upper()
    if 'USDT' in normalized and '/' not in normalized:
        normalized = normalized.replace('USDT', '/USDT')
    return normalized in SUPPORTED_PAIRS
