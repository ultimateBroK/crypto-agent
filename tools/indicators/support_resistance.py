from datetime import datetime
import numpy as np
from tools.utils.exchange import EXCHANGE


def get_support_resistance(coin: str, timeframe: str = '1h', lookback: int = 100, **kwargs):
    """Identify recent support/resistance zones using local highs/lows."""
    pair = f"{coin.upper().strip()}/USDT"
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=lookback)
    except Exception as e:
        return f"❌ Error OHLCV {pair}: {e}"
    
    if len(ohlcv) < 20:
        return f"⚠️ Not enough data for {pair}"
    
    highs = np.array([x[2] for x in ohlcv])
    lows = np.array([x[3] for x in ohlcv])
    
    window = 5
    resistance_levels = []
    support_levels = []
    
    for i in range(window, len(highs) - window):
        if highs[i] == max(highs[i-window:i+window+1]):
            resistance_levels.append(highs[i])
        if lows[i] == min(lows[i-window:i+window+1]):
            support_levels.append(lows[i])
    
    def cluster_levels(levels, tolerance=0.005):
        if not levels:
            return []
        levels = sorted(levels, reverse=True)
        clusters = []
        current_cluster = [levels[0]]
        for lvl in levels[1:]:
            if abs(lvl - current_cluster[-1]) / current_cluster[-1] < tolerance:
                current_cluster.append(lvl)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [lvl]
        clusters.append(sum(current_cluster) / len(current_cluster))
        return clusters[:5]
    
    res_clustered = cluster_levels(resistance_levels)
    sup_clustered = cluster_levels(support_levels)
    
    current_price = ohlcv[-1][4]
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    out = f"""🕐 {ts} Support/Resistance {pair}
Timeframe: {timeframe} | Lookback: {lookback} bars
Current Price: {current_price:.6f}

Resistance Zones (above price):
"""
    res_above = [r for r in res_clustered if r > current_price]
    if res_above:
        for idx, r in enumerate(res_above[:3], 1):
            out += f"  R{idx}: {r:.6f} (+{(r - current_price)/current_price*100:.2f}%)\n"
    else:
        out += "  None detected\n"
    
    out += "\nSupport Zones (below price):\n"
    sup_below = [s for s in sup_clustered if s < current_price]
    if sup_below:
        for idx, s in enumerate(sup_below[:3], 1):
            out += f"  S{idx}: {s:.6f} ({(s - current_price)/current_price*100:.2f}%)\n"
    else:
        out += "  None detected\n"
    
    return out


