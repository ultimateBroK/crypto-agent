"""
Shared helper functions for technical analysis calculations.
"""
from typing import List, Optional
import numpy as np


def sma(data: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average."""
    if len(data) < period or period <= 0:
        return None
    return sum(data[-period:]) / period


def ema(data: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average."""
    if len(data) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    ema_val = data[0]
    for price in data[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val


def wma(data: List[float], period: int) -> Optional[float]:
    """Calculate Weighted Moving Average."""
    if len(data) < period or period <= 0:
        return None
    weights = list(range(1, period + 1))
    window = data[-period:]
    return sum(w * x for w, x in zip(weights, window)) / sum(weights)


def hma(data: List[float], period: int) -> Optional[float]:
    """Calculate Hull Moving Average."""
    if period <= 0 or len(data) < period:
        return None
    half = max(1, period // 2)
    sqrtp = max(1, int(period ** 0.5))
    wma_half = wma(data, half)
    wma_full = wma(data, period)
    if wma_half is None or wma_full is None:
        return None
    series = data[:-1] + [2 * wma_half - wma_full]
    return wma(series, sqrtp)


def vwma(price: List[float], vol: List[float], period: int) -> Optional[float]:
    """Calculate Volume Weighted Moving Average."""
    if len(price) < period or len(vol) < period or period <= 0:
        return None
    pv = sum(p * v for p, v in zip(price[-period:], vol[-period:]))
    vv = sum(vol[-period:])
    if vv == 0:
        return None
    return pv / vv


def stddev(data: List[float], period: int) -> Optional[float]:
    """Calculate Standard Deviation."""
    if len(data) < period or period <= 1:
        return None
    window = data[-period:]
    m = sum(window) / period
    var = sum((x - m) ** 2 for x in window) / period
    return var ** 0.5


def rsi_calc(data: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index."""
    if len(data) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(data)):
        ch = data[i] - data[i - 1]
        gains.append(max(ch, 0))
        losses.append(abs(min(ch, 0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def stoch_k(highs: List[float], lows: List[float], closes: List[float], 
            k_len: int = 14, smooth_k: int = 3) -> Optional[float]:
    """Calculate Stochastic %K."""
    if len(closes) < k_len:
        return None
    hh = max(highs[-k_len:])
    ll = min(lows[-k_len:])
    if hh == ll:
        return 50.0
    raw_k = (closes[-1] - ll) / (hh - ll) * 100.0
    # Simple smoothing - in production, you'd calculate SMA of raw_k values
    return raw_k


def stoch_d(k_values: List[float], d_len: int = 3) -> Optional[float]:
    """Calculate Stochastic %D (SMA of %K)."""
    return sma(k_values, d_len)


def macd_calc(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD, Signal, and Histogram."""
    if len(data) < slow + signal:
        return None, None, None
    
    ema_fast_vals = []
    ema_slow_vals = []
    
    for i in range(len(data)):
        sub = data[:i + 1]
        ema_fast_vals.append(ema(sub, fast))
        ema_slow_vals.append(ema(sub, slow))
    
    macd_line = [
        (f - s) if f is not None and s is not None else None 
        for f, s in zip(ema_fast_vals, ema_slow_vals)
    ]
    
    macd_clean = [m for m in macd_line if m is not None]
    if len(macd_clean) < signal:
        return None, None, None
    
    # Calculate signal line
    signal_val = ema(macd_clean, signal)
    macd_val = macd_clean[-1]
    
    if signal_val is None or macd_val is None:
        return None, None, None
    
    hist_val = macd_val - signal_val
    return macd_val, signal_val, hist_val


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    """Calculate Average True Range."""
    if len(closes) < period + 1:
        return None
    
    true_ranges = []
    for i in range(1, len(closes)):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    
    return sum(true_ranges[-period:]) / period if len(true_ranges) >= period else None


def bollinger_bands(data: List[float], period: int = 20, std_dev: float = 2.0):
    """Calculate Bollinger Bands (upper, middle, lower)."""
    middle = sma(data, period)
    if middle is None:
        return None, None, None
    
    std = stddev(data, period)
    if std is None:
        return None, None, None
    
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return upper, middle, lower


def validate_period(period: int, min_val: int = 1, max_val: int = 500) -> bool:
    """Validate period parameter."""
    return isinstance(period, int) and min_val <= period <= max_val


def validate_data(data: List[float], min_len: int = 1) -> bool:
    """Validate data list."""
    return isinstance(data, list) and len(data) >= min_len and all(isinstance(x, (int, float)) for x in data)
