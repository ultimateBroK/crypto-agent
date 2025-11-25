import ccxt
from datetime import datetime
import numpy as np
from collections import defaultdict

EXCHANGE = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})


def get_volume_profile(coin: str, timeframe: str = '1h', lookback: int = 100, num_levels: int = 20, **kwargs):
    """Calculate Volume Profile - distribution of volume across price levels.
    
    Shows where most trading activity occurred (Point of Control, Value Area).
    
    Args:
        coin: Cryptocurrency symbol
        timeframe: Chart timeframe
        lookback: Number of bars to analyze
        num_levels: Number of price levels to divide range into
    
    Returns:
        POC (Point of Control), VAH (Value Area High), VAL (Value Area Low)
    """
    pair = f"{coin.upper().strip()}/USDT"
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=lookback)
    except ccxt.BaseError as e:
        return f"❌ Error OHLCV {pair}: {e}"
    
    if len(ohlcv) < 10:
        return f"⚠️ Not enough data for {pair}"
    
    # Extract data
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
    
    # Volume distribution by price level
    volume_at_price = defaultdict(float)
    
    for i in range(len(ohlcv)):
        # Distribute volume across the bar's range
        bar_high = highs[i]
        bar_low = lows[i]
        bar_vol = volumes[i]
        
        # Simple distribution: assume volume evenly distributed in bar range
        start_level = int((bar_low - price_min) / level_size)
        end_level = int((bar_high - price_min) / level_size)
        
        levels_in_bar = max(1, end_level - start_level + 1)
        vol_per_level = bar_vol / levels_in_bar
        
        for lvl in range(start_level, end_level + 1):
            if 0 <= lvl < num_levels:
                volume_at_price[lvl] += vol_per_level
    
    # Find POC (Point of Control) - price level with highest volume
    poc_level = max(volume_at_price.items(), key=lambda x: x[1])[0] if volume_at_price else 0
    poc_price = price_min + (poc_level + 0.5) * level_size
    poc_volume = volume_at_price[poc_level]
    
    # Calculate Value Area (70% of volume)
    total_volume = sum(volume_at_price.values())
    target_volume = total_volume * 0.70
    
    # Start from POC and expand outward
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
    
    # Position analysis
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


def get_order_flow(coin: str, limit: int = 50, **kwargs):
    """Analyze order flow and trade aggression from recent trades.
    
    Shows buy vs sell pressure, aggressor volume, and order flow imbalance.
    
    Args:
        coin: Cryptocurrency symbol
        limit: Number of recent trades to analyze
    
    Returns:
        Buy/sell volume ratio, aggressor analysis, delta
    """
    pair = f"{coin.upper().strip()}/USDT"
    try:
        trades = EXCHANGE.fetch_trades(pair, limit=limit)
    except ccxt.BaseError as e:
        return f"❌ Error trades {pair}: {e}"
    
    if not trades:
        return f"⚠️ No trades data for {pair}"
    
    buy_volume = 0
    sell_volume = 0
    buy_count = 0
    sell_count = 0
    
    total_cost = 0
    
    for trade in trades:
        side = trade.get('side')
        amount = trade.get('amount', 0)
        cost = trade.get('cost', 0)
        
        total_cost += cost
        
        if side == 'buy':
            buy_volume += amount
            buy_count += 1
        elif side == 'sell':
            sell_volume += amount
            sell_count += 1
    
    total_volume = buy_volume + sell_volume
    total_count = buy_count + sell_count
    
    if total_volume == 0:
        return f"⚠️ No volume in trades for {pair}"
    
    buy_pct = (buy_volume / total_volume) * 100
    sell_pct = (sell_volume / total_volume) * 100
    
    delta = buy_volume - sell_volume
    delta_pct = (delta / total_volume) * 100
    
    # Aggression analysis
    if buy_pct > 60:
        aggression = "Strong Buy Pressure"
        sentiment = "🟢 Bullish"
    elif buy_pct > 52:
        aggression = "Moderate Buy Pressure"
        sentiment = "🟢 Slightly Bullish"
    elif sell_pct > 60:
        aggression = "Strong Sell Pressure"
        sentiment = "🔴 Bearish"
    elif sell_pct > 52:
        aggression = "Moderate Sell Pressure"
        sentiment = "🔴 Slightly Bearish"
    else:
        aggression = "Balanced Flow"
        sentiment = "🟡 Neutral"
    
    avg_buy_size = buy_volume / buy_count if buy_count > 0 else 0
    avg_sell_size = sell_volume / sell_count if sell_count > 0 else 0
    
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    out = f"""🕐 {ts} Order Flow Analysis {pair}
Recent Trades: {total_count} ({limit} requested)

Volume Distribution:
  Buy Volume:  {buy_volume:.6f} ({buy_pct:.2f}%)
  Sell Volume: {sell_volume:.6f} ({sell_pct:.2f}%)
  Total Volume: {total_volume:.6f}

Order Flow Delta:
  Delta: {delta:+.6f} ({delta_pct:+.2f}%)

Trade Count:
  Buy Orders:  {buy_count} ({(buy_count/total_count*100):.1f}%)
  Sell Orders: {sell_count} ({(sell_count/total_count*100):.1f}%)

Average Trade Size:
  Avg Buy:  {avg_buy_size:.6f}
  Avg Sell: {avg_sell_size:.6f}

Total Value: ${total_cost:,.2f} USDT

💡 Analysis: {aggression}
Sentiment: {sentiment}
"""
    
    return out
