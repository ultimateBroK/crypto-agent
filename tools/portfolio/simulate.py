from datetime import datetime
from tools.utils.exchange import EXCHANGE


def simulate_portfolio_value(holdings: dict, quote: str = 'USDT', **kwargs):
    """Compute portfolio current value given coin:amount mapping (spot)."""
    if not holdings:
        return "⚠️ Provide holdings mapping {coin: amount}."
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [f"🧾 Portfolio Value ({quote})", f"🕐 {ts}"]
    total = 0.0
    for coin, amount in holdings.items():
        pair = f"{coin.upper().strip()}/{quote.upper()}"
        try:
            ticker = EXCHANGE.fetch_ticker(pair)
            price = ticker.get('last')
            if price is None:
                lines.append(f"{coin.upper():<6}: price unavailable")
                continue
            value = price * float(amount)
            total += value
            lines.append(f"{coin.upper():<6}: {amount} @ {price:.6f} = {value:.2f} {quote.upper()}")
        except Exception as e:
            lines.append(f"{coin.upper():<6}: ERR {e}")
    lines.append(f"Total: {total:.2f} {quote.upper()}")
    return '\n'.join(lines)


