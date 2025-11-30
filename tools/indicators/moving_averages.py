"""
Moving Average indicators with shared utilities and caching.
"""
from typing import Iterable, Optional
from tools.utils.exchange import fetch_closes
from tools.utils.helpers import sma, ema
from tools.utils.formatters import build_header, format_price, format_percentage
from tools.utils.constants import SMA_SHORT, SMA_MEDIUM, SMA_LONG
from tools.utils.nlp import resolve_timeframe


def get_sma(coin: str, timeframe: Optional[str] = None, periods: Iterable[int] = None, 
            limit: int = 300, **kwargs) -> str:
    """
    Calculate Simple Moving Averages for given periods.
    
    Args:
        coin: Cryptocurrency symbol
        timeframe: Candle timeframe
        periods: Tuple of periods to calculate (default: 20, 50, 100)
        limit: Number of candles to fetch
        
    Returns:
        Formatted SMA values string
    """
    if periods is None:
        periods = (SMA_SHORT, SMA_MEDIUM, SMA_LONG)
    
    pair = f"{coin.upper().strip()}/USDT"
    timeframe, tf_reason = resolve_timeframe(timeframe, default='1h', return_reason=True, **kwargs)
    closes, err = fetch_closes(pair, timeframe, limit, use_cache=True)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"

    last_close = closes[-1]
    header = build_header("SMA", pair, timeframe)
    lines = [header, f"Last Close: {format_price(last_close)}"]
    
    for p in periods:
        val = sma(closes, p)
        if val is None:
            lines.append(f"SMA{p}: insufficient data")
        else:
            diff = last_close - val
            diff_pct = (diff / val * 100) if val else 0
            lines.append(f"SMA{p}: {format_price(val)} Δ {diff:+.6f} ({format_percentage(diff_pct)})")
    
    if tf_reason:
        lines.append(f"\n⚠️ {tf_reason}")
    return '\n'.join(lines)


def get_ema_set(coin: str, timeframe: Optional[str] = None, periods: Iterable[int] = None,
               limit: int = 400, **kwargs) -> str:
    """
    Calculate Exponential Moving Averages for given periods.
    
    Args:
        coin: Cryptocurrency symbol
        timeframe: Candle timeframe
        periods: Tuple of periods to calculate (default: 34, 89, 200)
        limit: Number of candles to fetch
        
    Returns:
        Formatted EMA values string
    """
    if periods is None:
        periods = (34, 89, 200)
    
    pair = f"{coin.upper().strip()}/USDT"
    timeframe, tf_reason = resolve_timeframe(timeframe, default='1h', return_reason=True, **kwargs)
    closes, err = fetch_closes(pair, timeframe, limit, use_cache=True)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"

    last_close = closes[-1]
    header = build_header("EMA", pair, timeframe)
    lines = [header, f"Last Close: {format_price(last_close)}"]
    
    for p in periods:
        val = ema(closes, p)
        if val is None:
            lines.append(f"EMA{p}: insufficient data")
        else:
            diff = last_close - val
            diff_pct = (diff / val * 100) if val else 0
            lines.append(f"EMA{p}: {format_price(val)} Δ {diff:+.6f} ({format_percentage(diff_pct)})")
    
    if tf_reason:
        lines.append(f"\n⚠️ {tf_reason}")
    return '\n'.join(lines)


