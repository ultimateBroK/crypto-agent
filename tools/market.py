import ccxt
from datetime import datetime

EXCHANGE = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

def get_orderbook(coin: str, limit: int = 20, **kwargs):
    """Return top levels of order book for coin/USDT.
    Args: coin symbol, limit depth (max 100).
    """
    coin_sym = coin.upper().strip()
    pair = f"{coin_sym}/USDT"
    try:
        ob = EXCHANGE.fetch_order_book(pair, limit=limit)
        bids = ob.get('bids', [])[:limit]
        asks = ob.get('asks', [])[:limit]
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        def fmt(side):
            return '\n'.join(f"{p:.6f} x {a:.4f}" for p, a in side)
        return (
            f"📑 Order Book {pair}\n🕐 {ts}\n"\
            f"Depth (top {limit})\n"\
            f"Bids:\n{fmt(bids) if bids else 'None'}\n"\
            f"Asks:\n{fmt(asks) if asks else 'None'}\n"\
            f"Spread: {asks[0][0]-bids[0][0]:.6f} ({(asks[0][0]-bids[0][0])/asks[0][0]*100:.4f}%)" if bids and asks else "⚠️ No spread data"
        )
    except ccxt.BaseError as e:
        return f"❌ Error orderbook {pair}: {e}"


def get_recent_trades(coin: str, limit: int = 10, **kwargs):
    """Return recent trades for coin/USDT with price, size, side."""
    coin_sym = coin.upper().strip()
    pair = f"{coin_sym}/USDT"
    try:
        trades = EXCHANGE.fetch_trades(pair, limit=limit)
        ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        lines = []
        for t in trades[:limit]:
            side = t.get('side')
            price = t.get('price')
            amount = t.get('amount')
            cost = t.get('cost')
            lines.append(f"{side:<4} {price:.6f} x {amount:.6f} = {cost:.4f}")
        body = '\n'.join(lines) if lines else 'No trades'
        return f"📊 Recent Trades {pair}\n🕐 {ts}\n{body}"
    except ccxt.BaseError as e:
        return f"❌ Error trades {pair}: {e}"


def get_multi_prices(coins: list, **kwargs):
    """Return current prices for multiple coin symbols (USDT)."""
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    out = [f"🕐 {ts} Real-Time Prices"]
    for coin in coins:
        pair = f"{coin.upper().strip()}/USDT"
        try:
            ticker = EXCHANGE.fetch_ticker(pair)
            price = ticker.get('last')
            out.append(f"{coin.upper():<6}: {price:.6f} USDT")
        except Exception as e:
            out.append(f"{coin.upper():<6}: ERR {e}")
    return '\n'.join(out)
