"""
Enhanced exchange utilities with retry logic, validation, and caching.
"""
import ccxt
import time
from typing import List, Tuple, Optional, Dict, Any
from tools.utils.cache import cached, get_cache
from tools.utils.constants import (
    VALID_TIMEFRAMES, 
    MAX_OHLCV_LIMIT, 
    CACHE_TTL_SECONDS,
    DEFAULT_OHLCV_LIMIT
)


# Shared CCXT Gate client (spot)
EXCHANGE = ccxt.gate({
    'enableRateLimit': True, 
    'options': {'defaultType': 'spot'},
    'timeout': 30000,  # 30 second timeout
})


def validate_timeframe(timeframe: str) -> bool:
    """Validate if timeframe is supported."""
    return timeframe in VALID_TIMEFRAMES


def validate_pair(pair: str) -> Tuple[bool, str]:
    """Validate trading pair format."""
    if not pair or '/' not in pair:
        return False, "Invalid pair format. Expected format: SYMBOL/USDT"
    
    parts = pair.split('/')
    if len(parts) != 2:
        return False, "Invalid pair format. Expected format: SYMBOL/USDT"
    
    symbol, quote = parts
    if not symbol or not quote:
        return False, "Invalid pair format. Symbol and quote cannot be empty"
    
    return True, ""


def retry_on_error(func, max_retries: int = 3, delay: float = 1.0):
    """Retry function on error with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
        except ccxt.BaseError:
            raise
    return None


@cached(ttl=CACHE_TTL_SECONDS, prefix="ohlcv")
def fetch_ohlcv_cached(pair: str, timeframe: str, limit: int) -> List[List[float]]:
    """Fetch OHLCV data with caching."""
    def _fetch():
        return EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
    
    result = retry_on_error(_fetch)
    return result if result is not None else []


def fetch_ohlcv(pair: str, timeframe: str = '1h', limit: int = DEFAULT_OHLCV_LIMIT, 
                use_cache: bool = True) -> Tuple[Optional[List[List[float]]], Optional[str]]:
    """
    Fetch OHLCV data with validation, retry, and optional caching.
    
    Args:
        pair: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe
        limit: Number of candles to fetch
        use_cache: Whether to use cached data
    
    Returns:
        Tuple of (ohlcv_data, error_message)
    """
    # Validate inputs
    is_valid, error_msg = validate_pair(pair)
    if not is_valid:
        return None, f"❌ {error_msg}"
    
    if not validate_timeframe(timeframe):
        return None, f"❌ Invalid timeframe '{timeframe}'. Valid: {', '.join(VALID_TIMEFRAMES)}"
    
    if limit <= 0 or limit > MAX_OHLCV_LIMIT:
        return None, f"❌ Invalid limit {limit}. Must be between 1 and {MAX_OHLCV_LIMIT}"
    
    try:
        if use_cache:
            ohlcv = fetch_ohlcv_cached(pair, timeframe, limit)
        else:
            def _fetch():
                return EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
            ohlcv = retry_on_error(_fetch)
        
        if not ohlcv:
            return None, f"⚠️ No OHLCV data returned for {pair}"
        
        return ohlcv, None
        
    except ccxt.BadSymbol:
        return None, f"❌ Invalid trading pair: {pair} not found on exchange"
    except ccxt.NetworkError as e:
        return None, f"❌ Network error fetching {pair}: {str(e)}"
    except ccxt.BaseError as e:
        return None, f"❌ Exchange error for {pair}: {str(e)}"
    except Exception as e:
        return None, f"❌ Unexpected error fetching {pair}: {str(e)}"


def fetch_closes(pair: str, timeframe: str, limit: int, 
                use_cache: bool = True) -> Tuple[Optional[List[float]], Optional[str]]:
    """
    Fetch closing prices with validation and retry logic.
    
    Args:
        pair: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe
        limit: Number of candles to fetch
        use_cache: Whether to use cached data
    
    Returns:
        Tuple of (closes_list, error_message)
    """
    ohlcv, error = fetch_ohlcv(pair, timeframe, limit, use_cache)
    if error:
        return None, error
    
    if not ohlcv:
        return None, f"⚠️ No OHLCV data for {pair}"
    
    closes = [c[4] for c in ohlcv]
    return closes, None


def fetch_ticker(pair: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetch ticker data with validation and retry logic.
    
    Args:
        pair: Trading pair (e.g., 'BTC/USDT')
    
    Returns:
        Tuple of (ticker_data, error_message)
    """
    is_valid, error_msg = validate_pair(pair)
    if not is_valid:
        return None, f"❌ {error_msg}"
    
    try:
        def _fetch():
            return EXCHANGE.fetch_ticker(pair)
        
        ticker = retry_on_error(_fetch)
        if not ticker:
            return None, f"⚠️ No ticker data returned for {pair}"

        # Convert ccxt Ticker (mapping-like) into a plain dict for typing compatibility
        try:
            ticker_dict = dict(ticker)
        except Exception:
            if hasattr(ticker, "items"):
                ticker_dict = {k: v for k, v in ticker.items()}
            else:
                # Fallback: wrap raw object in a dict under key 'raw'
                ticker_dict = {"raw": ticker}

        return ticker_dict, None
        
    except ccxt.BadSymbol:
        return None, f"❌ Invalid trading pair: {pair} not found on exchange"
    except ccxt.NetworkError as e:
        return None, f"❌ Network error fetching {pair}: {str(e)}"
    except ccxt.BaseError as e:
        return None, f"❌ Exchange error for {pair}: {str(e)}"
    except Exception as e:
        return None, f"❌ Unexpected error fetching {pair}: {str(e)}"


def invalidate_cache(pair: Optional[str] = None):
    """
    Invalidate cache for specific pair or all cached data.
    
    Args:
        pair: Trading pair to invalidate, or None to clear all
    """
    cache = get_cache()
    if pair:
        # Invalidate all cache entries for this pair
        # This is a simple implementation - you might want to track keys more precisely
        cache.clear()
    else:
        cache.clear()


