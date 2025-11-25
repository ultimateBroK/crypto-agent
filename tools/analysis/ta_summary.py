from datetime import datetime
from tools.utils.exchange import EXCHANGE


def get_ta_summary(coin: str, timeframe: str = '1h', **kwargs):
    """Composite Technical Analysis summary combining oscillators, MAs, and pivots."""
    pair = f"{coin.upper().strip()}/USDT"
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=200)
    except Exception as e:
        return f"❌ Error OHLCV {pair}: {e}"
    
    if len(ohlcv) < 50:
        return f"⚠️ Not enough data for {pair}"
    
    closes = [x[4] for x in ohlcv]
    highs = [x[2] for x in ohlcv]
    lows = [x[3] for x in ohlcv]
    current = closes[-1]
    
    osc_buy = 0
    osc_sell = 0
    
    def calc_rsi(data, period=14):
        gains = [max(data[i] - data[i-1], 0) for i in range(1, len(data))]
        losses = [abs(min(data[i] - data[i-1], 0)) for i in range(1, len(data))]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    rsi = calc_rsi(closes)
    if rsi < 30:
        osc_buy += 1
    elif rsi > 70:
        osc_sell += 1
    
    def calc_stoch(highs, lows, closes, k=14):
        hh = max(highs[-k:])
        ll = min(lows[-k:])
        if hh == ll:
            return 50
        return ((closes[-1] - ll) / (hh - ll)) * 100
    
    stoch = calc_stoch(highs, lows, closes)
    if stoch < 20:
        osc_buy += 1
    elif stoch > 80:
        osc_sell += 1
    
    def calc_ema(data, period):
        k = 2 / (period + 1)
        ema = data[0]
        for price in data[1:]:
            ema = price * k + ema * (1 - k)
        return ema
    
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    macd_line = ema12 - ema26
    macd_prev = calc_ema(closes[:-1], 12) - calc_ema(closes[:-1], 26)
    if macd_line > macd_prev:
        osc_buy += 1
    else:
        osc_sell += 1
    
    mom = current - closes[-11] if len(closes) > 10 else 0
    if mom > 0:
        osc_buy += 1
    else:
        osc_sell += 1
    
    ma_buy = 0
    ma_sell = 0
    ma_periods = [5, 10, 20, 21, 30, 50, 55, 100, 200]
    for period in ma_periods:
        if len(closes) >= period:
            sma = sum(closes[-period:]) / period
            if current > sma:
                ma_buy += 1
            else:
                ma_sell += 1
    
    pivot_buy = 0
    pivot_sell = 0
    if len(ohlcv) >= 2:
        prev = ohlcv[-2]
        phigh, plow, pclose = prev[2], prev[3], prev[4]
        pp = (phigh + plow + pclose) / 3
        r1 = 2 * pp - plow
        s1 = 2 * pp - phigh
        
        if current > r1:
            pivot_buy += 1
        elif current < s1:
            pivot_sell += 1
    
    total_osc = 11
    total_ma = 17
    total_pivot = 4
    total = total_osc + total_ma + total_pivot
    
    osc_neutral = total_osc - osc_buy - osc_sell
    ma_neutral = total_ma - ma_buy - ma_sell
    pivot_neutral = total_pivot - pivot_buy - pivot_sell
    
    total_buy = osc_buy + ma_buy + pivot_buy
    total_sell = osc_sell + ma_sell + pivot_sell
    total_neutral = osc_neutral + ma_neutral + pivot_neutral
    
    buy_pct = (total_buy / total) * 100
    sell_pct = (total_sell / total) * 100
    neutral_pct = (total_neutral / total) * 100
    
    if buy_pct > 60 and osc_buy > osc_sell and ma_buy > ma_sell:
        overall = "STRONG BUY"
    elif buy_pct > 50:
        overall = "BUY"
    elif sell_pct > 60 and osc_sell > osc_buy and ma_sell > ma_buy:
        overall = "STRONG SELL"
    elif sell_pct > 50:
        overall = "SELL"
    else:
        overall = "NEUTRAL"
    
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    out = f"""🕐 {ts} Technical Analysis Summary {pair}
Timeframe: {timeframe}
Current Price: {current:.6f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Signal: {overall}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Score Breakdown:
  BUY:     {total_buy}/{total} ({buy_pct:.1f}%)
  SELL:    {total_sell}/{total} ({sell_pct:.1f}%)
  NEUTRAL: {total_neutral}/{total} ({neutral_pct:.1f}%)

Component Analysis:
  Oscillators ({total_osc}):
    BUY: {osc_buy} | SELL: {osc_sell} | NEUTRAL: {osc_neutral}
  
  Moving Averages ({total_ma}):
    BUY: {ma_buy} | SELL: {ma_sell} | NEUTRAL: {ma_neutral}
  
  Pivots ({total_pivot}):
    BUY: {pivot_buy} | SELL: {pivot_sell} | NEUTRAL: {pivot_neutral}

Key Indicators:
  RSI(14): {rsi:.2f} {"(Oversold)" if rsi < 30 else "(Overbought)" if rsi > 70 else "(Neutral)"}
  Stochastic: {stoch:.2f}
  MACD: {"Bullish" if macd_line > macd_prev else "Bearish"}
  Momentum(10): {mom:+.6f}
"""
    return out


