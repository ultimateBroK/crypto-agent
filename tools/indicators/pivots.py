from datetime import datetime
from typing import Optional
from tools.utils.exchange import EXCHANGE
from tools.utils.nlp import resolve_timeframe


def get_pivot_points(coin: str, timeframe: Optional[str] = None, pivot_type: str = 'traditional', **kwargs):
    """Calculate pivot points (support/resistance levels) for the coin."""
    pair = f"{coin.upper().strip()}/USDT"
    timeframe, tf_reason = resolve_timeframe(timeframe, default='1d', return_reason=True, **kwargs)
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=2)
    except Exception as e:
        return f"❌ Error OHLCV {pair}: {e}"
    
    if len(ohlcv) < 2:
        return f"⚠️ Not enough data for {pair}"
    
    prev = ohlcv[-2]
    phigh, plow, pclose = prev[2], prev[3], prev[4]
    popen = prev[1]
    
    if pivot_type == 'traditional':
        pp = (phigh + plow + pclose) / 3
        r1 = 2 * pp - plow
        s1 = 2 * pp - phigh
        r2 = pp + (phigh - plow)
        s2 = pp - (phigh - plow)
        r3 = phigh + 2 * (pp - plow)
        s3 = plow - 2 * (phigh - pp)
    elif pivot_type == 'fibonacci':
        pp = (phigh + plow + pclose) / 3
        r1 = pp + (phigh - plow) * 0.382
        s1 = pp - (phigh - plow) * 0.382
        r2 = pp + (phigh - plow) * 0.618
        s2 = pp - (phigh - plow) * 0.618
        r3 = pp + (phigh - plow) * 1.000
        s3 = pp - (phigh - plow) * 1.000
    elif pivot_type == 'woodie':
        pp = (phigh + plow + 2 * popen) / 4
        r1 = 2 * pp - plow
        s1 = 2 * pp - phigh
        r2 = pp + (phigh - plow)
        s2 = pp - (phigh - plow)
        r3 = phigh + 2 * (pp - plow)
        s3 = plow - 2 * (phigh - pp)
    elif pivot_type == 'camarilla':
        pp = (phigh + plow + pclose) / 3
        r1 = pclose + (phigh - plow) * 1.1 / 12
        s1 = pclose - (phigh - plow) * 1.1 / 12
        r2 = pclose + (phigh - plow) * 1.1 / 6
        s2 = pclose - (phigh - plow) * 1.1 / 6
        r3 = pclose + (phigh - plow) * 1.1 / 4
        s3 = pclose - (phigh - plow) * 1.1 / 4
    else:
        return f"⚠️ Unknown pivot type: {pivot_type}"
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    current = ohlcv[-1][4]
    
    out = f"""🕐 {ts} Pivot Points {pair} ({pivot_type.title()})
Timeframe: {timeframe}
Current Price: {current:.6f}

Pivot Point (PP): {pp:.6f}
Resistance Levels:
  R1: {r1:.6f}
  R2: {r2:.6f}
  R3: {r3:.6f}
Support Levels:
  S1: {s1:.6f}
  S2: {s2:.6f}
  S3: {s3:.6f}
"""
    if current > r1:
        out += f"\n💡 Price above R1 (bullish zone)"
    elif current < s1:
        out += f"\n💡 Price below S1 (bearish zone)"
    else:
        out += f"\n💡 Price between S1-R1 (neutral)"
    
    if tf_reason:
        out += f"\n⚠️ {tf_reason}"
    return out


