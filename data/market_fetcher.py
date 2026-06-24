"""
market_fetcher.py - TITAN Wave 2A
Fetches OHLCV data. READ ONLY. No trading.
"""
import os
import ccxt
import pandas as pd
import logging
import asyncio

logger = logging.getLogger(__name__)

# Supported exchanges configuration
SUPPORTED_EXCHANGES = {
    'kraken': {
        'class': ccxt.kraken,
        'quote': 'USD',
        'symbol_map': {'USDT': 'USD'}
    },
    'binance': {
        'class': ccxt.binance,
        'quote': 'USDT',
        'symbol_map': {},
        'options': {'defaultType': 'spot'}
    },
    'okx': {
        'class': ccxt.okx,
        'quote': 'USDT',
        'symbol_map': {}
    },
    'bybit': {
        'class': ccxt.bybit,
        'quote': 'USDT',
        'symbol_map': {}
    },
    'kucoin': {
        'class': ccxt.kucoin,
        'quote': 'USDT',
        'symbol_map': {}
    }
}

# User-facing supported pairs (USDT notation)
SUPPORTED_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT',
    'SOL/USDT', 'ADA/USDT', 'XRP/USDT'
]

# Dynamic exchange initialization
def _get_exchange():
    """Initialize the configured exchange from DATA_SOURCE env variable."""
    data_source = os.getenv('DATA_SOURCE', 'kraken').lower()
    
    if data_source not in SUPPORTED_EXCHANGES:
        logger.warning(f"Unknown DATA_SOURCE '{data_source}', defaulting to kraken")
        data_source = 'kraken'
    
    config = SUPPORTED_EXCHANGES[data_source]
    exchange_class = config['class']
    
    # Build exchange configuration
    exchange_config = {'enableRateLimit': True}
    if 'options' in config:
        exchange_config.update(config['options'])
    
    logger.info(f"[EXCHANGE] Using {data_source}")
    return exchange_class(exchange_config), data_source, config

EXCHANGE, DATA_SOURCE_NAME, EXCHANGE_CONFIG = _get_exchange()

def _map_symbol(symbol: str) -> str:
    """Map symbol between exchanges (e.g., BTC/USDT -> BTC/USD for Kraken)."""
    # Normalize input symbol
    normalized = symbol.upper()
    if 'USDT' in normalized and '/' not in normalized:
        normalized = normalized.replace('USDT', '/USDT')
    
    # Apply symbol mapping if needed
    symbol_map = EXCHANGE_CONFIG.get('symbol_map', {})
    for old_quote, new_quote in symbol_map.items():
        if old_quote in normalized:
            normalized = normalized.replace(old_quote, new_quote)
            break
    
    return normalized

async def fetch_ohlcv(
    symbol: str,
    timeframe: str,
    limit: int = 200
) -> pd.DataFrame:
    mapped_symbol = _map_symbol(symbol)
    logger.info(f"[FETCH START] {symbol} -> {mapped_symbol} ({timeframe})")
    
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda: EXCHANGE.fetch_ohlcv(
                mapped_symbol, timeframe, limit=limit
            )
        )
        
        if not raw:
            logger.warning(f"[FETCH EMPTY] No data for {mapped_symbol} {timeframe}")
            return pd.DataFrame()
        
        logger.info(f"[FETCH SUCCESS] Got {len(raw)} candles for {mapped_symbol}")
        
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
        return df
        
    except Exception as e:
        logger.error(f"[FETCH ERROR] {symbol} ({mapped_symbol}): {type(e).__name__}: {e}")
        return pd.DataFrame()

def is_supported(symbol: str) -> bool:
    """Check if symbol is supported (user-facing check, always USDT notation)."""
    normalized = symbol.upper()
    if 'USDT' in normalized and '/' not in normalized:
        normalized = normalized.replace('USDT', '/USDT')
    return normalized in SUPPORTED_PAIRS
