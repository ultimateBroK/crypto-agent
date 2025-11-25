import ccxt
from datetime import datetime

try:
    import talib
except ImportError:
    talib = None

EXCHANGE = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})


def _fetch_closes(pair: str, timeframe: str, limit: int):
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
    except ccxt.BaseError as e:
        return None, f"❌ Error OHLCV {pair}: {e}"
    if not ohlcv:
        return None, f"⚠️ No OHLCV data for {pair}"
    closes = [c[4] for c in ohlcv]
    return closes, None


def get_sma(coin: str, timeframe: str = '1h', periods=(20, 50, 100), limit: int = 300, **kwargs):
    pair = f"{coin.upper().strip()}/USDT"
    closes, err = _fetch_closes(pair, timeframe, limit)
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


def get_ema_set(coin: str, timeframe: str = '1h', periods=(34, 89, 200), limit: int = 400, **kwargs):
    pair = f"{coin.upper().strip()}/USDT"
    closes, err = _fetch_closes(pair, timeframe, limit)
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


def get_rsi(coin: str, timeframe: str = '1h', period: int = 14, limit: int = 300, **kwargs):
    pair = f"{coin.upper().strip()}/USDT"
    closes, err = _fetch_closes(pair, timeframe, limit)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"
    if len(closes) < period + 1:
        return f"⚠️ Not enough data for RSI{period}"
    if talib:
        import numpy as np
        rsi_val = float(talib.RSI(np.array(closes, dtype='float64'), timeperiod=period)[-1])
    else:
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    status = 'Overbought' if rsi_val >= 70 else 'Oversold' if rsi_val <= 30 else 'Neutral'
    return f"🕐 {ts} RSI {pair} timeframe={timeframe}\nRSI{period}: {rsi_val:.2f} ({status})"


def get_macd(coin: str, timeframe: str = '1h', fast: int = 12, slow: int = 26, signal: int = 9, limit: int = 400, **kwargs):
    pair = f"{coin.upper().strip()}/USDT"
    closes, err = _fetch_closes(pair, timeframe, limit)
    if err:
        return err
    if not closes:
        return f"⚠️ No close data for {pair}"
    if talib:
        import numpy as np
        macd, macd_signal, macd_hist = talib.MACD(np.array(closes, dtype='float64'), fastperiod=fast, slowperiod=slow, signalperiod=signal)
        macd_val = float(macd[-1])
        signal_val = float(macd_signal[-1])
        hist_val = float(macd_hist[-1])
    else:
        def ema(seq, n):
            if len(seq) < n:
                return None
            k = 2 / (n + 1)
            e = seq[0]
            for price in seq[1:]:
                e = price * k + e * (1 - k)
            return e
        if len(closes) < slow + signal:
            return "⚠️ Not enough data for MACD"
        ema_fast = []
        ema_slow = []
        for i in range(len(closes)):
            sub = closes[: i + 1]
            ema_fast.append(ema(sub, fast))
            ema_slow.append(ema(sub, slow))
        macd_line = [ (f - s) if f is not None and s is not None else None for f, s in zip(ema_fast, ema_slow) ]
        macd_clean = [m for m in macd_line if m is not None]
        if len(macd_clean) < signal:
            return "⚠️ Not enough MACD values for signal"
        signal_line = []
        k = 2 / (signal + 1)
        e = macd_clean[0]
        for v in macd_clean[1:]:
            e = v * k + e * (1 - k)
            signal_line.append(e)
        macd_val = macd_clean[-1]
        signal_val = signal_line[-1]
        hist_val = macd_val - signal_val
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    momentum = 'Bullish' if macd_val > signal_val else 'Bearish' if macd_val < signal_val else 'Flat'
    return f"🕐 {ts} MACD {pair} timeframe={timeframe}\nMACD({fast},{slow},{signal}): {macd_val:.6f}\nSignal: {signal_val:.6f}\nHistogram: {hist_val:+.6f}\nMomentum: {momentum}"
