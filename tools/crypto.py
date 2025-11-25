import ccxt
from datetime import datetime

# Tool: get_crypto_price

def get_crypto_price(coin: str, **kwargs):
    """Fetches REAL-TIME, LATEST price data of a SINGLE cryptocurrency from Binance.

    (Docstring shortened: logic unchanged from original.)
    """
    print(f"Tool 'get_crypto_price' was called with coin: {coin}!")

    if not coin or not coin.strip():
        return "❌ Error: Please provide a valid cryptocurrency symbol (e.g., 'BTC', 'ETH', 'XRP').\n\nReasoning: The coin parameter was empty or invalid. A valid symbol is required to fetch price data."

    try:
        binance = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        coin_upper = coin.upper().strip()
        trading_pair = f"{coin_upper}/USDT"
        fetch_timestamp = datetime.now()
        ticker = binance.fetch_ticker(trading_pair)
        ticker_timestamp = ticker.get('timestamp')

        price = ticker.get('last')
        high_24h = ticker.get('high')
        low_24h = ticker.get('low')
        change_24h = ticker.get('change')
        change_percent_24h = ticker.get('percentage')
        volume_24h = ticker.get('quoteVolume')

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

            if ticker_timestamp:
                try:
                    data_time = datetime.fromtimestamp(ticker_timestamp / 1000 if ticker_timestamp > 1e10 else ticker_timestamp)
                    time_str = data_time.strftime("%Y-%m-%d %H:%M:%S UTC")
                except (ValueError, OSError, TypeError):
                    time_str = fetch_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                time_str = fetch_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

            response = f"""📊 {coin_upper} Price Analysis (Binance)
🕐 Data Fetched: {time_str} (Real-Time)

💰 Current Price: ${price:,.2f} USDT

📈 24-Hour Performance:
   • Change: ${change_24h:+,.2f} ({change_percent_24h:+.2f}%)"""
            if high_24h is not None and low_24h is not None:
                range_value = high_24h - low_24h
                range_percent = (range_value / price * 100) if price > 0 else 0.0
                response += f"""
   • High: ${high_24h:,.2f} USDT
   • Low: ${low_24h:,.2f} USDT
   • Range: ${range_value:,.2f} USDT ({range_percent:.2f}% of current price)"""

            response += f"""

📊 Trading Volume (24h): ${volume_24h:,.2f} USDT

💡 Market Context:
"""
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

            response += f"\n\n✅ Data Source: Binance Exchange (Real-Time) | Trading Pair: {trading_pair}"
            response += "\n🔄 Note: This data is fetched fresh from Binance exchange in real-time. No cached data is used."
            return response
        else:
            return f"⚠️ Could not retrieve price data for {coin_upper}.\n\nReasoning: The ticker data was fetched but the 'last' price field was missing. This may indicate a data issue with the exchange."

    except ccxt.BaseError as e:
        print(f"ERROR in get_crypto_price: {e}")
        error_msg = str(e)
        return f"""❌ Error fetching price for {coin.upper().strip()}

Reasoning: 
• Attempted to fetch data from Binance exchange
• The trading pair {coin.upper().strip()}/USDT may not exist or may be unavailable
• Exchange returned error: {error_msg}

Possible causes:
• Invalid cryptocurrency symbol
• Trading pair not available on Binance
• Temporary exchange API issue

💡 Suggestion: Verify the coin symbol is correct and available on Binance."""

    except Exception as e:
        print(f"ERROR in get_crypto_price: {e}")
        return f"""❌ Unexpected error occurred while fetching price for {coin}

Reasoning:
• An unexpected error occurred during the price fetch operation
• Error details: {str(e)}

💡 Suggestion: Please verify the coin symbol is valid and try again. If the issue persists, there may be a network or system problem."""