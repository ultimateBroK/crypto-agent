import ccxt
from typing import List, Tuple, Optional


# Shared CCXT Binance client (spot)
EXCHANGE = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})


def fetch_closes(pair: str, timeframe: str, limit: int) -> Tuple[Optional[List[float]], Optional[str]]:
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
    except ccxt.BaseError as e:
        return None, f"❌ Error OHLCV {pair}: {e}"
    if not ohlcv:
        return None, f"⚠️ No OHLCV data for {pair}"
    closes = [c[4] for c in ohlcv]
    return closes, None


