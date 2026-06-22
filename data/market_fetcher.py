"""
market_fetcher.py - TITAN Wave 2A
Fetches OHLCV data. READ ONLY. No trading.
"""
import ccxt
import pandas as pd
import logging
import asyncio

logger = logging.getLogger(__name__)

EXCHANGE = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

SUPPORTED_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT',
    'SOL/USDT', 'ADA/USDT', 'XRP/USDT'
]

async def fetch_ohlcv(
    symbol: str,
    timeframe: str,
    limit: int = 200
) -> pd.DataFrame:
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: EXCHANGE.fetch_ohlcv(
                symbol, timeframe, limit=limit
            )
        )
        if not raw:
            logger.warning(f"No data for {symbol} {timeframe}")
            return pd.DataFrame()
        df = pd.DataFrame(
            raw,
            columns=['timestamp','open','high',
                     'low','close','volume']
        )
        df['timestamp'] = pd.to_datetime(
            df['timestamp'], unit='ms'
        )
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        logger.info(f"Fetched {len(df)} candles for {symbol} {timeframe}")
        return df
    except Exception as e:
        logger.error(f"Fetch failed {symbol} {timeframe}: {e}")
        return pd.DataFrame()

def is_supported(symbol: str) -> bool:
    normalized = symbol.upper()
    if 'USDT' in normalized and '/' not in normalized:
        normalized = normalized.replace('USDT', '/USDT')
    return normalized in SUPPORTED_PAIRS
