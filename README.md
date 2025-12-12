## Cryage Agent
Smart, modular crypto analysis agent powered by Agno. Fetch real-time market data, run technical analysis, monitor alerts, analyze order flow/volume, and simulate portfolio value — all via natural language or direct tool calls.

### Highlights
- **Fast Real-time Data**: Gate via CCXT with robust retry logic.
- **High Performance**: In-memory TTL caching for expensive API calls and indicators.
- **Modular Architecture**: Domain-driven design (market, indicators, analysis, alerts, portfolio) with shared utilities.
- **Flexible Interface**: Works with natural language prompts or Python calls.
- **Clean Outputs**: Standardized formatting optimized for quick decision-making.

## Project Structure
```
config/
  settings.py          # Constants, model id, description
agents/
  cryage.py            # create_agent() factory
server/
  app.py               # AgentOS setup, FastAPI app, serve helper
tools/
  utils/
    cache.py           # Caching decorators (TTL)
    constants.py       # Shared constants and configuration
    exchange.py        # Shared CCXT client with retry logic
    formatters.py      # Output formatting helpers
    helpers.py         # Shared calculation logic (TA, Math)
  market/
    prices.py          # Single/multi price tools
    depth.py           # Orderbook, recent trades
    flow.py            # Order flow analysis
  indicators/
    moving_averages.py # SMA/EMA sets
    momentum.py        # RSI, MACD
    pivots.py          # Pivot points
    support_resistance.py # S/R zones
    volume.py          # Volume profile levels (POC/VAH/VAL)
  analysis/
    forecast.py        # Linear regression forecasting
    ta_summary.py      # Composite TA summary
  alerts/
    price_alerts.py    # Price alert management
  portfolio/
    simulate.py        # Portfolio valuation
indicators/            # Pine script resources (unchanged)
main.py                # Thin entrypoint exposing `app`
requirements.txt       # Dependencies
```

## Quick Start
Run the development server with auto-reload:
```bash
uvicorn main:app --reload
```
Or use helper serve (same effect):
```bash
python main.py
```

## Architecture & Features
- **Shared Utilities**: Common logic for indicators (RSI, EMA, etc.) is centralized in `tools/utils/helpers.py` to reduce duplication.
- **Caching**: Heavy operations like fetching OHLCV data or calculating complex indicators are cached using `@cached` from `tools/utils/cache.py` to improve response times.
- **Resilience**: Network requests via `tools/utils/exchange.py` include exponential backoff retries to handle API rate limits and transient errors.
- **Standardization**: All tools use `tools/utils/formatters.py` to ensure consistent output formats (dates, numbers, percentages).

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
| `get_ict_killzones(date_yyyy_mm_dd, timezone, reference_timezone, profile)` | Show ICT Killzones (Asia/London/NY) converted to your timezone |
| `set_price_alert(coin, condition, price, message)` | Create price threshold alert |
| `list_alerts(coin)` | List all active price alerts |
| `remove_alert(alert_id)` | Remove specific price alert |
| `check_alerts(coin)` | Check alerts against current prices |
| `simulate_portfolio_value({coin: amount})` | Aggregate portfolio valuation in USDT |

## Tool Usage Examples
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
get_ict_killzones(date_yyyy_mm_dd="2025-12-12", timezone="UTC")
set_price_alert("BTC", condition="above", price=50000, message="BTC breakout!")
list_alerts()
list_alerts(coin="BTC")
check_alerts()
check_alerts(coin="ETH")
remove_alert("BTC_above_50000_1234567890.123")
simulate_portfolio_value({"BTC":0.12, "ETH":2.3, "SOL":15})
```

## Natural Language Examples
You can interact with the agent using conversational language:

**Market Analysis**
- "Is BTC in a downtrend on the 4h chart? Check EMA alignment and RSI."
- "Scan SOL for a potential reversal. Look at MACD divergence and support levels on the 1h."
- "What's the volume profile for BTC looking like over the last 3 days? Where is the Point of Control?"
- "Give me a full technical summary for ETH on the daily timeframe."

**Execution & Liquidity**
- "I'm looking for a scalp entry on ETH. Check the order book depth and recent trade flow."
- "Analyze the order flow delta for BTC. Are buyers aggressive right now?"
- "Show me the top 20 levels of the order book for SOL."

**Alerts & Monitoring**
- "Set a trap for BTC. Alert me if it crosses above $98,000 with a message 'ATH Breakout'."
- "Monitor ETH for a drop below $2,500. Label it 'Support Failure'."
- "List all my active price alerts."

**Portfolio & Forecasting**
- "How much is my portfolio worth? I have 0.5 BTC, 10 ETH, and 500 SOL."
- "Forecast the price of BNB for the next 12 hours based on the last 200 data points."

## Playbooks (End-to-End Use Cases)

### 1. Swing Trade Setup (Trend Following)
**Goal**: Identify a high-probability trend continuation entry.
1. **Trend Check**: "Analyze the daily trend for SOL using EMAs and Pivot Points." -> `get_ema_set`, `get_pivot_points`
2. **Momentum Confirmation**: "Check 4h RSI and MACD for momentum confirmation." -> `get_rsi`, `get_macd`
3. **Level Finding**: "Identify key support zones to place a stop loss." -> `get_support_resistance`
4. **Decision**: Enter if price pulls back to support while trend remains bullish.

### 2. Scalping the Breakout (High Volatility)
**Goal**: Catch a rapid price move through a key level.
1. **Setup**: "Monitor BTC price alerts for a cross above $60,000." -> `set_price_alert`
2. **Validation (On Alert)**: "Immediately check the order book for sell wall absorption." -> `get_orderbook`
3. **Confirmation**: "Analyze recent order flow delta to confirm buyer aggression." -> `get_order_flow`
4. **Execution**: Enter on high buy volume delta; exit quickly if flow stalls.

### 3. DCA & Portfolio Management
**Goal**: Passive accumulation and value tracking.
1. **Valuation**: "What is the current value of 0.1 BTC and 5 ETH?" -> `simulate_portfolio_value`
2. **Dip Buying**: "Check if BTC is oversold on the daily timeframe (RSI < 30) for a potential DCA entry." -> `get_rsi`
3. **Health Check**: "Give me a technical summary for BTC to see if the long-term trend is still intact." -> `get_ta_summary`

### 4. ICT Killzone Liquidity Sweep (Scalp Timing)
**Goal**: Use ICT Killzones as a timing filter for liquidity/volatility.
1. **Timing**: "Show me today's ICT Killzones in UTC." -> `get_ict_killzones`
2. **Setup Context**: "During the London Kill Zone, check BTC EMA alignment (1h) and key pivots (1d)." -> `get_ema_set`, `get_pivot_points`
3. **Liquidity + Reaction**: "If price sweeps a prior high/low in a killzone, confirm with order flow delta and orderbook." -> `get_order_flow`, `get_orderbook`
4. **Risk**: Prefer tight invalidation around the sweep level; avoid forcing trades outside killzones unless trend is strong.

## Indicator Interpretation Hints
- **EMA alignment**: Price above all EMAs suggests strong uptrend; below indicates downtrend.
- **RSI**: >70 typically overbought; <30 oversold; 45-55 neutral zone.
- **MACD**: Histogram turning from negative to positive signals potential bullish reversal; opposite for bearish.
- **Volume Profile**: POC (Point of Control) is highest volume level; VAH/VAL define 70% value area where most trading occurred.
- **Order Flow**: Positive delta (more buy aggression) suggests institutional accumulation; negative delta indicates distribution.
- **Price Alerts**: Use 'above'/'below' for one-time checks; 'crosses_above'/'crosses_below' for crossing detection.

## Adding Tools
1. Create a file under the right subpackage `tools/<subpackage>/` (e.g., `tools/market/depth.py` or `tools/indicators/momentum.py`).
2. Import the tool function in `agents/cryage.py` and append it to the `tools=[...]` list.
3. Restart the server.

## Changing Model
Edit `MODEL_ID` in `config/settings.py`.

## Notes
- `app` is exposed at module path `main:app`.
- Real-time price tool logic preserved exactly (only relocated).
