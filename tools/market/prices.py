"""
Real-time cryptocurrency price fetching with improved error handling and caching.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from tools.utils.exchange import EXCHANGE, fetch_ticker
from tools.utils.formatters import format_timestamp, format_price, format_percentage


def get_crypto_price(coin: str, **kwargs) -> str:
    """
    Fetch REAL-TIME price data of a SINGLE cryptocurrency from Gate.
    
    Args:
        coin: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'XRP')
        
    Returns:
        Formatted price analysis string with real-time data
    """
    print(f"Tool 'get_crypto_price' was called with coin: {coin}!")
    
    if not coin or not coin.strip():
        return "❌ Error: Please provide a valid cryptocurrency symbol (e.g., 'BTC', 'ETH', 'XRP').\n\nReasoning: The coin parameter was empty or invalid. A valid symbol is required to fetch price data."
    
    coin_upper = coin.upper().strip()
    trading_pair = f"{coin_upper}/USDT"
    fetch_timestamp = datetime.now()
    
    # Use shared fetch_ticker utility
    ticker, error = fetch_ticker(trading_pair)
    if error:
        return f"{error}\n\nReasoning: Failed to fetch ticker data from Gate exchange."
    
    # Extract ticker data (guard against missing/invalid ticker)
    if not ticker or not isinstance(ticker, dict):
        return f"⚠️ Could not retrieve ticker data for {trading_pair}.\n\nReasoning: fetch_ticker returned no data or an unexpected response."
    ticker_timestamp = ticker.get('timestamp')
    price = ticker.get('last')
    high_24h = ticker.get('high')
    low_24h = ticker.get('low')
    change_24h = ticker.get('change')
    change_percent_24h = ticker.get('percentage')
    volume_24h = ticker.get('quoteVolume')
    
    # Parse and validate numeric values
    if price is not None:
        try:
            price = float(price) if price is not None else None
            high_24h = float(high_24h) if high_24h is not None else None
            low_24h = float(low_24h) if low_24h is not None else None
            change_24h = float(change_24h) if change_24h is not None else 0.0
            change_percent_24h = float(change_percent_24h) if change_percent_24h is not None else 0.0
            volume_24h = float(volume_24h) if volume_24h is not None else 0.0
        except (ValueError, TypeError):
            return f"⚠️ Could not parse price data for {coin_upper}.\n\nReasoning: The ticker data contained invalid numeric values."
        
        if price is None:
            return f"⚠️ Could not retrieve price data for {coin_upper}.\n\nReasoning: The ticker data was fetched but the price field was missing or invalid."
        
        # Format timestamp
        if ticker_timestamp:
            try:
                data_time = datetime.fromtimestamp(ticker_timestamp / 1000 if ticker_timestamp > 1e10 else ticker_timestamp)
                time_str = data_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            except (ValueError, OSError, TypeError):
                time_str = fetch_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            time_str = fetch_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Build response
        response = f"""📊 {coin_upper} Price Analysis (Gate)
🕐 Data Fetched: {time_str} (Real-Time)

💰 Current Price: ${format_price(price, 2)} USDT

📈 24-Hour Performance:
   • Change: ${change_24h:+,.2f} ({format_percentage(change_percent_24h)})"""
        
        if high_24h is not None and low_24h is not None:
            range_value = high_24h - low_24h
            range_percent = (range_value / price * 100) if price > 0 else 0.0
            response += f"""
   • High: ${format_price(high_24h, 2)} USDT
   • Low: ${format_price(low_24h, 2)} USDT
   • Range: ${format_price(range_value, 2)} USDT ({range_percent:.2f}% of current price)"""
        
        response += f"""

📊 Trading Volume (24h): ${format_price(volume_24h, 2)} USDT

💡 Market Context:
"""
        
        # Market context analysis
        if change_percent_24h > 0:
            response += f"   • {coin_upper} is up {change_percent_24h:.2f}% in the last 24 hours, showing positive momentum."
        elif change_percent_24h < 0:
            response += f"   • {coin_upper} is down {abs(change_percent_24h):.2f}% in the last 24 hours, showing negative pressure."
        else:
            response += f"   • {coin_upper} price is relatively stable with minimal change."
        
        if high_24h is not None and low_24h is not None and price > 0:
            price_range = high_24h - low_24h
            if price_range > 0:
                price_position = ((price - low_24h) / price_range) * 100
                if price_position > 75:
                    high_percent = (price / high_24h) * 100 if high_24h > 0 else 0
                    response += f"\n   • Current price is near the 24h high ({high_percent:.1f}% of high)."
                elif price_position < 25:
                    low_percent = (price / low_24h) * 100 if low_24h > 0 else 0
                    response += f"\n   • Current price is near the 24h low ({low_percent:.1f}% of low)."
                else:
                    response += "\n   • Current price is in the middle range of the 24h trading band."
        
        response += f"\n\n✅ Data Source: Gate Exchange (Real-Time) | Trading Pair: {trading_pair}"
        response += "\n🔄 Note: This data is fetched fresh from Gate exchange in real-time. No cached data is used."
        
        return response
    else:
        return f"⚠️ Could not retrieve price data for {coin_upper}.\n\nReasoning: The ticker data was fetched but the 'last' price field was missing. This may indicate a data issue with the exchange."


def get_multi_prices(coins: str, **kwargs) -> str:
    """
    Fetch prices for multiple cryptocurrencies.
    
    Args:
        coins: Comma-separated list of coin symbols (e.g., 'BTC,ETH,XRP')
        
    Returns:
        Formatted multi-price summary
    """
    if not coins or not coins.strip():
        return "❌ Error: Please provide coin symbols separated by commas (e.g., 'BTC,ETH,XRP')."
    
    coin_list = [c.strip().upper() for c in coins.split(',') if c.strip()]
    if not coin_list:
        return "❌ Error: No valid coin symbols provided."
    
    ts = format_timestamp()
    results = [f"🕐 {ts} Multi-Coin Price Summary\n"]
    
    for coin_symbol in coin_list:
        pair = f"{coin_symbol}/USDT"
        ticker, error = fetch_ticker(pair)
        
        if error or not ticker or not isinstance(ticker, dict):
            results.append(f"❌ {coin_symbol}: Failed to fetch")
            continue
        
        price = ticker.get('last')
        change_pct = ticker.get('percentage', 0)
        
        if price:
            emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            results.append(f"{emoji} {coin_symbol}: ${format_price(price, 2)} ({format_percentage(change_pct)})")
        else:
            results.append(f"⚠️ {coin_symbol}: Price unavailable")
    
    return '\n'.join(results)

