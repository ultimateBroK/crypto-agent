from datetime import datetime
from typing import Iterable, Tuple

try:
    import talib
except ImportError:
    talib = None

from tools.utils.exchange import fetch_closes


def get_sma(coin: str, timeframe: str = '1h', periods: Iterable[int] = (20, 50, 100), limit: int = 300, **kwargs):
    pair = f"{coin.upper().strip()}/USDT"
    closes, err = fetch_closes(pair, timeframe, limit)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"

    def sma(data, n):
        if len(data) < n:
            return None
        return sum(data[-n:]) / n

    last_close = closes[-1]
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [f"🕐 {ts} SMA {pair} timeframe={timeframe}", f"Last Close: {last_close:.6f}"]
    for p in periods:
        val = sma(closes, p)
        if val is None:
            lines.append(f"SMA{p}: insufficient data")
        else:
            diff = last_close - val
            diff_pct = diff / val * 100 if val else 0
            lines.append(f"SMA{p}: {val:.6f} Δ {diff:+.6f} ({diff_pct:+.2f}%)")
    return '\n'.join(lines)


def get_ema_set(coin: str, timeframe: str = '1h', periods: Iterable[int] = (34, 89, 200), limit: int = 400, **kwargs):
    pair = f"{coin.upper().strip()}/USDT"
    closes, err = fetch_closes(pair, timeframe, limit)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"

    def ema(data, n):
        if len(data) < n:
            return None
        if talib:
            import numpy as np
            return float(talib.EMA(np.array(data, dtype='float64'), timeperiod=n)[-1])
        k = 2 / (n + 1)
        e = data[0]
        for price in data[1:]:
            e = price * k + e * (1 - k)
        return e

    last_close = closes[-1]
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [f"🕐 {ts} EMA {pair} timeframe={timeframe}", f"Last Close: {last_close:.6f}"]
    for p in periods:
        val = ema(closes, p)
        if val is None:
            lines.append(f"EMA{p}: insufficient data")
        else:
            diff = last_close - val
            diff_pct = diff / val * 100 if val else 0
            lines.append(f"EMA{p}: {val:.6f} Δ {diff:+.6f} ({diff_pct:+.2f}%)")
    return '\n'.join(lines)


