"""
Momentum indicators with shared utilities and caching.
"""
from typing import Optional
from tools.utils.exchange import fetch_closes
from tools.utils.helpers import rsi_calc, macd_calc
from tools.utils.formatters import (
    build_header, get_rsi_status, get_macd_momentum
)
from tools.utils.constants import (
    RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL
)
from tools.utils.nlp import resolve_timeframe


def get_rsi(coin: str, timeframe: Optional[str] = None, period: int = None,
           limit: int = 300, **kwargs) -> str:
    """
    Calculate Relative Strength Index.
    
    Args:
        coin: Cryptocurrency symbol
        timeframe: Candle timeframe
        period: RSI period (default: 14)
        limit: Number of candles to fetch
        
    Returns:
        Formatted RSI value string
    """
    if period is None:
        period = RSI_PERIOD
    
    pair = f"{coin.upper().strip()}/USDT"
    timeframe, tf_reason = resolve_timeframe(timeframe, default='1h', return_reason=True, **kwargs)
    closes, err = fetch_closes(pair, timeframe, limit, use_cache=True)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"
    if len(closes) < period + 1:
        return f"⚠️ Not enough data for RSI{period}. Need at least {period + 1} candles."
    
    rsi_val = rsi_calc(closes, period)
    if rsi_val is None:
        return f"⚠️ Could not calculate RSI{period}"
    
    header = build_header("RSI", pair, timeframe)
    status = get_rsi_status(rsi_val)
    
    result = f"{header}\nRSI{period}: {rsi_val:.2f} ({status})"
    if tf_reason:
        result += f"\n⚠️ {tf_reason}"
    return result


def get_macd(coin: str, timeframe: Optional[str] = None, fast: int = None, slow: int = None,
            signal: int = None, limit: int = 400, **kwargs) -> str:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        coin: Cryptocurrency symbol
        timeframe: Candle timeframe
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)
        limit: Number of candles to fetch
        
    Returns:
        Formatted MACD values string
    """
    if fast is None:
        fast = MACD_FAST
    if slow is None:
        slow = MACD_SLOW
    if signal is None:
        signal = MACD_SIGNAL
    
    pair = f"{coin.upper().strip()}/USDT"
    timeframe, tf_reason = resolve_timeframe(timeframe, default='1h', return_reason=True, **kwargs)
    closes, err = fetch_closes(pair, timeframe, limit, use_cache=True)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"
    
    macd_val, signal_val, hist_val = macd_calc(closes, fast, slow, signal)
    
    if macd_val is None or signal_val is None or hist_val is None:
        return f"⚠️ Not enough data for MACD({fast},{slow},{signal}). Need at least {slow + signal} candles."
    
    header = build_header("MACD", pair, timeframe)
    momentum = get_macd_momentum(macd_val, signal_val)
    
    result = (
        f"{header}\nMACD({fast},{slow},{signal}): {macd_val:.6f}\n"
        f"Signal: {signal_val:.6f}\nHistogram: {hist_val:+.6f}\nMomentum: {momentum}"
    )
    if tf_reason:
        result += f"\n⚠️ {tf_reason}"
    return result


