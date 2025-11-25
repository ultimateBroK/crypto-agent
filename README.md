# Cryage Agent (Modular Agno Structure)

## Structure
```
config/
  settings.py          # Constants, model id, description
agents/
  cryage.py            # create_agent() factory
server/
  app.py               # AgentOS setup, FastAPI app, serve helper
tools/
  crypto.py            # get_crypto_price tool
  market.py            # Multi-price, orderbook, recent trades
  technical.py         # SMA, EMA, RSI, MACD indicators
  portfolio.py         # Portfolio valuation
  analysis.py          # Pivot points, S/R, forecasting
  signals.py           # Composite TA summary
  volume.py            # Volume profile, order flow analysis
  alerts.py            # Price alert management
indicators/            # Pine script resources (unchanged)
main.py                # Thin entrypoint exposing `app`
requirements.txt       # Dependencies
```

## Usage
Run development server with auto-reload:
```bash
uvicorn main:app --reload
```
Or use helper serve (same effect):
```bash
python main.py
```

## Available Tools
| Tool | Purpose |
|------|---------|
| `get_crypto_price(coin)` | Real-time detailed single coin price analysis |
| `get_multi_prices(coins)` | Fetch prices for multiple coins quickly |
| `get_orderbook(coin, limit)` | Top order book levels + spread |
| `get_recent_trades(coin, limit)` | Recent trades with side, size, cost |
| `get_sma(coin, timeframe, periods)` | Simple moving averages and deviation |
| `get_ema_set(coin, timeframe)` | EMA 34/89/200 trend alignment |
| `get_rsi(coin, timeframe, period)` | RSI momentum and overbought/oversold |
| `get_macd(coin, timeframe)` | MACD line, signal, histogram momentum |
| `get_pivot_points(coin, timeframe, type)` | Calculate pivot support/resistance levels |
| `get_support_resistance(coin, timeframe)` | Detect key S/R zones from price action |
| `get_forecast(coin, timeframe, train_len)` | Linear regression price forecast |
| `get_ta_summary(coin, timeframe)` | Composite TA signal (oscillators+MAs+pivots) |
| `get_volume_profile(coin, timeframe, lookback, num_levels)` | POC, VAH, VAL volume distribution analysis |
| `get_order_flow(coin, limit)` | Buy/sell aggressor volume and order flow delta |
| `set_price_alert(coin, condition, price, message)` | Create price threshold alert |
| `list_alerts(coin)` | List all active price alerts |
| `remove_alert(alert_id)` | Remove specific price alert |
| `check_alerts(coin)` | Check alerts against current prices |
| `simulate_portfolio_value({coin: amount})` | Aggregate portfolio valuation in USDT |

### Tool Usage Examples
```python
get_multi_prices(["BTC","ETH","SOL"])
get_orderbook("BTC", limit=10)
get_recent_trades("ETH", limit=15)
get_sma("SOL", timeframe="15m", periods=(20,50))
get_ema_set("BTC", timeframe="1h")
get_rsi("ETH", timeframe="4h", period=14)
get_macd("ADA", timeframe="1h")
get_pivot_points("BTC", timeframe="1d", pivot_type="traditional")
get_support_resistance("ETH", timeframe="4h", lookback=100)
get_forecast("SOL", timeframe="1h", train_len=100, forecast_len=10)
get_ta_summary("BTC", timeframe="1h")
get_volume_profile("BTC", timeframe="1h", lookback=100, num_levels=20)
get_order_flow("ETH", limit=50)
set_price_alert("BTC", condition="above", price=50000, message="BTC breakout!")
list_alerts()
list_alerts(coin="BTC")
check_alerts()
check_alerts(coin="ETH")
remove_alert("BTC_above_50000_1234567890.123")
simulate_portfolio_value({"BTC":0.12, "ETH":2.3, "SOL":15})
```

### Natural Language Query Examples
You can ask the agent:
- "Analyze BTC trend with EMA 34/89/200" → triggers `get_ema_set`.
- "Give me RSI and MACD for ETH on 4h timeframe" → triggers `get_rsi` + `get_macd`.
- "Compare current SOL price with SMA20 and SMA50" → triggers `get_sma`.
- "Calculate BTC pivot points for daily timeframe" → triggers `get_pivot_points`.
- "Find support and resistance zones for ETH" → triggers `get_support_resistance`.
- "Forecast BTC price for next 10 bars" → triggers `get_forecast`.
- "Technical analysis summary for BTC" → triggers `get_ta_summary`.
- "Show BTC volume profile for last 100 hours" → triggers `get_volume_profile`.
- "Analyze ETH order flow from recent trades" → triggers `get_order_flow`.
- "Alert me when BTC crosses above $50,000" → triggers `set_price_alert`.
- "Check all my price alerts" → triggers `check_alerts`.
- "List my BTC alerts" → triggers `list_alerts`.
- "Total portfolio value: BTC 0.1, ETH 2, SOL 10" → triggers `simulate_portfolio_value`.
- "BTC order book top 10 levels" → triggers `get_orderbook`.

### Indicator Interpretation Hints
- **EMA alignment**: Price above all EMAs suggests strong uptrend; below indicates downtrend.
- **RSI**: >70 typically overbought; <30 oversold; 45-55 neutral zone.
- **MACD**: Histogram turning from negative to positive signals potential bullish reversal; opposite for bearish.
- **Volume Profile**: POC (Point of Control) is highest volume level; VAH/VAL define 70% value area where most trading occurred.
- **Order Flow**: Positive delta (more buy aggression) suggests institutional accumulation; negative delta indicates distribution.
- **Price Alerts**: Use 'above'/'below' for one-time checks; 'crosses_above'/'crosses_below' for crossing detection.

## Adding Tools
1. Create new file in `tools/` (e.g. `tools/orderbook.py`).
2. Import it in `agents/cryage.py` and append to `tools=[...]` list.
3. Restart server.

## Changing Model
Edit `MODEL_ID` in `config/settings.py`.

## Notes
- `app` is exposed at module path `main:app`.
- Real-time price tool logic preserved exactly (only relocated).
