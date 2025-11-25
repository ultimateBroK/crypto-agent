from datetime import datetime
from tools.utils.exchange import EXCHANGE


def get_order_flow(coin: str, limit: int = 50, **kwargs):
    """Analyze order flow and trade aggression from recent trades."""
    pair = f"{coin.upper().strip()}/USDT"
    try:
        trades = EXCHANGE.fetch_trades(pair, limit=limit)
    except Exception as e:
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


