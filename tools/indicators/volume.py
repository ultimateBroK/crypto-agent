from datetime import datetime
from collections import defaultdict
from tools.utils.exchange import EXCHANGE


def get_volume_profile(coin: str, timeframe: str = '1h', lookback: int = 100, num_levels: int = 20, **kwargs):
    """Calculate Volume Profile - distribution of volume across price levels."""
    pair = f"{coin.upper().strip()}/USDT"
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=lookback)
    except Exception as e:
        return f"❌ Error OHLCV {pair}: {e}"
    
    if len(ohlcv) < 10:
        return f"⚠️ Not enough data for {pair}"
    
    highs = [x[2] for x in ohlcv]
    lows = [x[3] for x in ohlcv]
    closes = [x[4] for x in ohlcv]
    volumes = [x[5] for x in ohlcv]
    
    price_min = min(lows)
    price_max = max(highs)
    price_range = price_max - price_min
    
    if price_range == 0:
        return f"⚠️ Invalid price range for {pair}"
    
    level_size = price_range / num_levels
    volume_at_price = defaultdict(float)
    
    for i in range(len(ohlcv)):
        bar_high = highs[i]
        bar_low = lows[i]
        bar_vol = volumes[i]
        
        start_level = int((bar_low - price_min) / level_size)
        end_level = int((bar_high - price_min) / level_size)
        
        levels_in_bar = max(1, end_level - start_level + 1)
        vol_per_level = bar_vol / levels_in_bar
        
        for lvl in range(start_level, end_level + 1):
            if 0 <= lvl < num_levels:
                volume_at_price[lvl] += vol_per_level
    
    poc_level = max(volume_at_price.items(), key=lambda x: x[1])[0] if volume_at_price else 0
    poc_price = price_min + (poc_level + 0.5) * level_size
    poc_volume = volume_at_price[poc_level]
    
    total_volume = sum(volume_at_price.values())
    target_volume = total_volume * 0.70
    
    value_area_levels = {poc_level}
    accumulated_volume = poc_volume
    
    above = poc_level + 1
    below = poc_level - 1
    
    while accumulated_volume < target_volume:
        vol_above = volume_at_price.get(above, 0) if above < num_levels else 0
        vol_below = volume_at_price.get(below, 0) if below >= 0 else 0
        
        if vol_above == 0 and vol_below == 0:
            break
        
        if vol_above >= vol_below and above < num_levels:
            value_area_levels.add(above)
            accumulated_volume += vol_above
            above += 1
        elif below >= 0:
            value_area_levels.add(below)
            accumulated_volume += vol_below
            below -= 1
        else:
            break
    
    vah_level = max(value_area_levels) if value_area_levels else poc_level
    val_level = min(value_area_levels) if value_area_levels else poc_level
    
    vah_price = price_min + (vah_level + 0.5) * level_size
    val_price = price_min + (val_level + 0.5) * level_size
    
    current_price = closes[-1]
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    if current_price > vah_price:
        position = "Above Value Area (bullish)"
    elif current_price < val_price:
        position = "Below Value Area (bearish)"
    elif abs(current_price - poc_price) / poc_price < 0.005:
        position = "At POC (equilibrium)"
    else:
        position = "Within Value Area (consolidation)"
    
    out = f"""🕐 {ts} Volume Profile {pair}
Timeframe: {timeframe} | Lookback: {lookback} bars
Current Price: {current_price:.6f}

Volume Profile Levels:
  POC (Point of Control): {poc_price:.6f}
  VAH (Value Area High):  {vah_price:.6f}
  VAL (Value Area Low):   {val_price:.6f}

Value Area: {val_price:.6f} - {vah_price:.6f}
Value Area Width: {((vah_price - val_price) / poc_price * 100):.2f}%

Total Volume Analyzed: {total_volume:,.0f}
Volume at POC: {poc_volume:,.0f} ({(poc_volume/total_volume*100):.1f}%)

💡 Price Position: {position}
"""
    return out


