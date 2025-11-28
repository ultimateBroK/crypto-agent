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
    
    opens = [x[1] for x in ohlcv]
    highs = [x[2] for x in ohlcv]
    lows = [x[3] for x in ohlcv]
    closes = [x[4] for x in ohlcv]
    volumes = [x[5] for x in ohlcv]
    current = closes[-1]
    
    # ---------- helpers ----------
    def sma(data, period):
        if len(data) < period or period <= 0:
            return None
        return sum(data[-period:]) / period
    
    def ema(data, period):
        if len(data) < period or period <= 0:
            return None
        k = 2 / (period + 1)
        ema_val = data[0]
        for price in data[1:]:
            ema_val = price * k + ema_val * (1 - k)
        return ema_val
    
    def wma(data, period):
        if len(data) < period or period <= 0:
            return None
        weights = list(range(1, period + 1))
        window = data[-period:]
        return sum(w * x for w, x in zip(weights, window)) / sum(weights)
    
    def hma(data, period):
        if period <= 0 or len(data) < period:
            return None
        half = max(1, period // 2)
        sqrtp = max(1, int(period ** 0.5))
        wma_half = wma(data, half)
        wma_full = wma(data, period)
        if wma_half is None or wma_full is None:
            return None
        series = data[:-1] + [2 * (wma_half if wma_half is not None else 0) - (wma_full if wma_full is not None else 0)]
        return wma(series, sqrtp)
    
    def vwma(price, vol, period):
        if len(price) < period or len(vol) < period or period <= 0:
            return None
        pv = sum(p * v for p, v in zip(price[-period:], vol[-period:]))
        vv = sum(vol[-period:])
        if vv == 0:
            return None
        return pv / vv
    
    def stddev(data, period):
        if len(data) < period or period <= 1:
            return None
        window = data[-period:]
        m = sum(window) / period
        var = sum((x - m) ** 2 for x in window) / period
        return var ** 0.5
    
    def rsi_series(data, period=14):
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
    
    def stoch_k(highs_, lows_, closes_, k_len=14, smooth_k=3):
        if len(closes_) < k_len:
            return None
        hh = max(highs_[-k_len:])
        ll = min(lows_[-k_len:])
        if hh == ll:
            raw_k = 50.0
        else:
            raw_k = (closes_[-1] - ll) / (hh - ll) * 100.0
        # simple smoothing by SMA on last smooth_k of raw; with one point, just raw
        # For simplicity, use SMA over last smooth_k raw values by approximating with same value
        return raw_k if smooth_k <= 1 else raw_k
    
    def cci(src_, period=20):
        if len(src_) < period:
            return None
        ma = sma(src_, period)
        sd = stddev(src_, period)
        if ma is None or sd is None or sd == 0:
            return None
        return (src_[-1] - ma) / (0.015 * sd)
    
    def true_range(h, l, c):
        trs = []
        for i in range(1, len(c)):
            tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
            trs.append(tr)
        return trs
    
    def adx_di(highs_, lows_, closes_, period=14):
        if len(closes_) < period + 2:
            return None, None, None
        dm_plus = []
        dm_minus = []
        for i in range(1, len(highs_)):
            up = highs_[i] - highs_[i - 1]
            down = lows_[i - 1] - lows_[i]
            dm_plus.append(up if (up > down and up > 0) else 0.0)
            dm_minus.append(down if (down > up and down > 0) else 0.0)
        trs = true_range(highs_, lows_, closes_)
        if len(trs) < period:
            return None, None, None
        def rma(series, length):
            if len(series) < length:
                return None
            alpha = 1.0 / length
            val = series[0]
            for x in series[1:]:
                val = alpha * x + (1 - alpha) * val
            return val
        tr_rma = rma(trs, period)
        dmp_rma = rma(dm_plus, period)
        dmn_rma = rma(dm_minus, period)
        if tr_rma in (None, 0.0):
            return None, None, None
        dip = 100.0 * (dmp_rma / tr_rma) if dmp_rma is not None else None
        dim = 100.0 * (dmn_rma / tr_rma) if dmn_rma is not None else None
        if dip is None or dim is None:
            return None, None, None
        dx = 100.0 * abs(dip - dim) / max(dip + dim, 1e-9)
        # smooth DX roughly (single value approximation)
        adx_val = dx
        return dip, dim, adx_val
    
    def ao_value(highs_, lows_):
        hl2 = [(h + l) / 2.0 for h, l in zip(highs_, lows_)]
        sma5 = sma(hl2, 5)
        sma34 = sma(hl2, 34)
        if sma5 is None or sma34 is None:
            return None
        return sma5 - sma34
    
    def macd_hist(closes_):
        ema12 = ema(closes_, 12)
        ema26 = ema(closes_, 26)
        if ema12 is None or ema26 is None:
            return None, None, None
        macd_line = ema12 - ema26
        # proxy for signal: EMA9 of MACD line via recompute on closes_ pairs
        macd_series = []
        e12 = closes_[0]
        e26 = closes_[0]
        k12 = 2 / (12 + 1)
        k26 = 2 / (26 + 1)
        for price in closes_:
            e12 = price * k12 + e12 * (1 - k12)
            e26 = price * k26 + e26 * (1 - k26)
            macd_series.append(e12 - e26)
        signal = ema(macd_series, 9)
        if signal is None:
            return None, None, None
        hist = macd_series[-1] - signal
        hist_prev = macd_series[-2] - ema(macd_series[:-1], 9) if len(macd_series) > 10 else None
        return macd_series[-1], signal, (hist, hist_prev)
    
    def stoch_rsi_k(closes_, rlen=14, stochlen=14, smooth=3):
        if len(closes_) < rlen + stochlen:
            return None
        # build RSI series
        rsi_vals = []
        gains = []
        losses = []
        for i in range(1, len(closes_)):
            ch = closes_[i] - closes_[i - 1]
            gains.append(max(ch, 0))
            losses.append(abs(min(ch, 0)))
        # simple rolling RSI approximation for last window
        for i in range(rlen, len(closes_)):
            g = sum(gains[i - rlen:i]) / rlen
            l = sum(losses[i - rlen:i]) / rlen
            if l == 0:
                rsi_vals.append(100.0)
            else:
                rs = g / l
                rsi_vals.append(100.0 - (100.0 / (1.0 + rs)))
        if len(rsi_vals) < stochlen:
            return None
        hh = max(rsi_vals[-stochlen:])
        ll = min(rsi_vals[-stochlen:])
        if hh == ll:
            rawk = 50.0
        else:
            rawk = (rsi_vals[-1] - ll) / (hh - ll) * 100.0
        return rawk if smooth <= 1 else rawk
    
    def williams_r(highs_, lows_, closes_, period=14):
        if len(closes_) < period:
            return None
        hh = max(highs_[-period:])
        ll = min(lows_[-period:])
        if hh == ll:
            return 0.0
        return 100.0 * (closes_[-1] - hh) / (hh - ll)
    
    def ultimate_osc(highs_, lows_, closes_, a=7, b=14, c=28):
        if len(closes_) < c + 1:
            return None
        def calc_bp_tr(i):
            high_ = max(highs_[i], closes_[i - 1])
            low_ = min(lows_[i], closes_[i - 1])
            bp = closes_[i] - low_
            tr = high_ - low_
            return bp, tr
        def avg_bp_tr(length):
            bp_sum = 0.0
            tr_sum = 0.0
            for i in range(len(closes_) - length, len(closes_)):
                bp, tr = calc_bp_tr(i)
                bp_sum += bp
                tr_sum += tr
            return (bp_sum / tr_sum) if tr_sum != 0 else 0.0
        avg7 = avg_bp_tr(a)
        avg14 = avg_bp_tr(b)
        avg28 = avg_bp_tr(c)
        return 100.0 * (4 * avg7 + 2 * avg14 + avg28) / 7.0
    
    def ichimoku_baseline(closes_, period=26):
        if len(highs) < period or len(lows) < period:
            return None
        return (max(highs[-period:]) + min(lows[-period:])) / 2.0
    
    # ---------- Oscillators (11) ----------
    osc_buy = 0
    osc_sell = 0
    
    # 1. RSI(14)
    rsi = rsi_series(closes, 14)
    if rsi < 30:
        osc_buy += 1
    elif rsi > 70:
        osc_sell += 1
    
    # 2. Stochastic %K (14,3,3) - use %K vs 20/80
    stoch = stoch_k(highs, lows, closes, 14, 3)
    if stoch < 20:
        osc_buy += 1
    elif stoch > 80:
        osc_sell += 1
    
    # 3. CCI(20) using stddev to match Pine usage
    cci_val = cci(closes, 20)
    if cci_val is not None:
        if cci_val < -100:
            osc_buy += 1
        elif cci_val > 100:
            osc_sell += 1
    
    # 4. ADX/DI (14) threshold 25
    di_plus, di_minus, adx_val = adx_di(highs, lows, closes, 14)
    if None not in (di_plus, di_minus, adx_val):
        if adx_val > 25:
            if di_plus > di_minus:
                osc_buy += 1
            elif di_minus > di_plus:
                osc_sell += 1
    
    # 5. Awesome Oscillator
    ao = ao_value(highs, lows)
    if ao is not None:
        if ao > 0:
            osc_buy += 1
        elif ao < 0:
            osc_sell += 1
    
    # 6. Momentum(10)
    mom = current - closes[-11] if len(closes) > 10 else 0
    if mom > 0:
        osc_buy += 1
    else:
        osc_sell += 1
    
    # 7. MACD histogram slope
    macd_line, macd_signal, hist_pair = macd_hist(closes)
    if hist_pair is not None and hist_pair[1] is not None:
        hist_cur, hist_prev = hist_pair
        if hist_cur > hist_prev:
            osc_buy += 1
        else:
            osc_sell += 1
    
    # 8. Stoch RSI Fast (3,3,14,14) - compare K to 20/80
    sr_k = stoch_rsi_k(closes, 14, 14, 3)
    if sr_k is not None:
        if sr_k < 20:
            osc_buy += 1
        elif sr_k > 80:
            osc_sell += 1
    
    # 9. Williams %R (14) thresholds -80/-20
    wr = williams_r(highs, lows, closes, 14)
    if wr is not None:
        if wr < -80:
            osc_buy += 1
        elif wr > -20:
            osc_sell += 1
    
    # 10. Bull/Bear Power proxy (Elder-based): SMA(30) of (bull-bear) sign
    # bull = high - EMA(13), bear = low - EMA(13)
    ema13 = ema(closes, 13)
    if ema13 is not None:
        bull = highs[-1] - ema13
        bear = lows[-1] - ema13
        # build synthetic series for last 30 periods if possible
        if len(closes) >= 30:
            ema_series = []
            e = closes[0]
            k13 = 2 / (13 + 1)
            for price in closes:
                e = price * k13 + e * (1 - k13)
                ema_series.append(e)
            bb_series = []
            for i in range(len(closes)):
                bb_series.append((highs[i] - ema_series[i]) - (lows[i] - ema_series[i]))
            bb_sma30 = sma(bb_series, 30)
            if bb_sma30 is not None and bb_sma30 > 0:
                osc_buy += 1
            else:
                osc_sell += 1
        else:
            if (bull - bear) > 0:
                osc_buy += 1
            else:
                osc_sell += 1
    
    # 11. Ultimate Oscillator (7,14,28) thresholds 30/70
    uo = ultimate_osc(highs, lows, closes, 7, 14, 28)
    if uo is not None:
        if uo < 30:
            osc_buy += 1
        elif uo > 70:
            osc_sell += 1
    
    # Present oscillators total count
    total_osc = 11
    
    # ---------- Moving Averages (17) ----------
    ma_buy = 0
    ma_sell = 0
    ma_possible = 0
    def add_ma_signal(val):
        nonlocal ma_buy, ma_sell, ma_possible
        if val is None:
            return
        ma_possible += 1
        if current > val:
            ma_buy += 1
        else:
            ma_sell += 1
    
    add_ma_signal(ema(closes, 5))      # EMA(5)
    add_ma_signal(sma(closes, 5))      # SMA(5)
    add_ma_signal(ema(closes, 10))     # EMA(10)
    add_ma_signal(sma(closes, 10))     # SMA(10)
    add_ma_signal(ema(closes, 21))     # EMA(21)
    add_ma_signal(sma(closes, 20))     # SMA(20)
    add_ma_signal(ema(closes, 30))     # EMA(30)
    add_ma_signal(sma(closes, 30))     # SMA(30)
    add_ma_signal(ema(closes, 55))     # EMA(55)
    add_ma_signal(sma(closes, 50))     # SMA(50)
    add_ma_signal(ema(closes, 100))    # EMA(100)
    add_ma_signal(sma(closes, 100))    # SMA(100)
    add_ma_signal(ema(closes, 200))    # EMA(200)
    add_ma_signal(sma(closes, 200))    # SMA(200)
    add_ma_signal(ichimoku_baseline(closes, 26))  # Ichimoku baseline (26)
    add_ma_signal(vwma(closes, volumes, 20))      # VWMA(20)
    add_ma_signal(hma(closes, 9))                 # HMA(9)
    
    total_ma = ma_possible  # dynamically count only what was computable (up to 17)
    
    # ---------- Pivots (4) ----------
    pivot_buy = 0
    pivot_sell = 0
    pivot_possible = 0
    if len(ohlcv) >= 2:
        prev = ohlcv[-2]
        p_open, p_high, p_low, p_close = prev[1], prev[2], prev[3], prev[4]
        # Traditional
        tr_pp = (p_high + p_low + p_close) / 3.0
        tr_r1 = tr_pp + tr_pp - p_low
        tr_s1 = tr_pp - (p_high - tr_pp)
        pivot_possible += 1
        if current > tr_r1:
            pivot_buy += 1
        elif current < tr_s1:
            pivot_sell += 1
        # Fibonacci
        fib_pp = tr_pp
        range_ = (p_high - p_low)
        fib_r1 = fib_pp + range_ * 0.382
        fib_s1 = fib_pp - range_ * 0.382
        pivot_possible += 1
        if current > fib_r1:
            pivot_buy += 1
        elif current < fib_s1:
            pivot_sell += 1
        # Woodie
        wo_pp = (p_high + p_low + 2 * p_open) / 4.0
        wo_r1 = wo_pp + wo_pp - p_low
        wo_s1 = wo_pp - (p_high - wo_pp)
        pivot_possible += 1
        if current > wo_r1:
            pivot_buy += 1
        elif current < wo_s1:
            pivot_sell += 1
        # Camarilla
        cam_pp = (p_high + p_low + p_close) / 3.0
        cam_r1 = p_close + (p_high - p_low) * 1.1 / 12.0
        cam_s1 = p_close - (p_high - p_low) * 1.1 / 12.0
        pivot_possible += 1
        if current > cam_r1:
            pivot_buy += 1
        elif current < cam_s1:
            pivot_sell += 1
    total_pivot = pivot_possible
    
    # ---------- Totals ----------
    total = total_osc + total_ma + total_pivot
    
    osc_neutral = total_osc - osc_buy - osc_sell
    ma_neutral = total_ma - ma_buy - ma_sell
    pivot_neutral = total_pivot - pivot_buy - pivot_sell
    
    total_buy = osc_buy + ma_buy + pivot_buy
    total_sell = osc_sell + ma_sell + pivot_sell
    total_neutral = osc_neutral + ma_neutral + pivot_neutral
    
    buy_pct = (total_buy / total) * 100 if total > 0 else 0.0
    sell_pct = (total_sell / total) * 100 if total > 0 else 0.0
    neutral_pct = (total_neutral / total) * 100 if total > 0 else 0.0
    
    # Pine-like points (scaled 0..10)
    buy_point = (total_buy / total) * 10.0 if total > 0 else 0.0
    sell_point = (total_sell / total) * 10.0 if total > 0 else 0.0
    
    # ---------- Overall signal (approx. Pine logic) ----------
    if buy_pct > 60 and osc_buy > osc_sell and ma_buy > ma_sell and pivot_buy >= pivot_sell:
        overall = "STRONG BUY"
    elif buy_pct > 50:
        overall = "BUY"
    elif sell_pct > 60 and osc_sell > osc_buy and ma_sell > ma_buy and pivot_sell >= pivot_buy:
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

Points (0..10):
  BUY:  {buy_point:.2f}
  SELL: {sell_point:.2f}

Component Analysis:
  Oscillators ({total_osc} of 11):
    BUY: {osc_buy} | SELL: {osc_sell} | NEUTRAL: {osc_neutral}
  
  Moving Averages ({total_ma} of 17):
    BUY: {ma_buy} | SELL: {ma_sell} | NEUTRAL: {ma_neutral}
  
  Pivots ({total_pivot} of 4):
    BUY: {pivot_buy} | SELL: {pivot_sell} | NEUTRAL: {pivot_neutral}

Key Indicators:
  RSI(14): {rsi:.2f} {"(Oversold)" if rsi < 30 else "(Overbought)" if rsi > 70 else "(Neutral)"}
  Stochastic %K(14,3,3): {stoch:.2f}
  MACD Hist Slope: {"Bullish" if (hist_pair and hist_pair[1] is not None and hist_pair[0] > hist_pair[1]) else "Bearish"}
  Momentum(10): {mom:+.6f}
"""
    return out


