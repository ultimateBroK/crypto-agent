# Cryage Agent - AI Coding Guide

## Architecture Overview

**Cryage** is a crypto analysis agent powered by **Agno framework** + **Ollama**, designed with a modular, domain-driven architecture. The system fetches real-time market data from Gate via CCXT, performs technical analysis, and exposes both natural language and REST API interfaces.

**Key Stack**: FastAPI + Agno + Ollama + CCXT (Gate) + TA-Lib + NumPy/Polars
**Future Stack**: QuestDB (time-series), PostgreSQL/Neon (relational), Pinecone (vector search)

### Three-Layer Architecture

```
Presentation Layer: Agno Tools (NL interface) + FastAPI (REST/WebSocket)
      ↓
Business Logic Layer: Services + Data Pipelines
      ↓
Data Layer: Repositories → QuestDB (time-series) + PostgreSQL (relational)
```

**Current State**: Tools directly access CCXT via shared utilities. Planned refactor introduces service/repository layers for future database integration.

## Critical Dependency: TA-Lib Installation

**System-level requirement before pip install**:
```bash
# Linux/Ubuntu
sudo apt-get install ta-lib

# macOS
brew install ta-lib

# Windows: Download from https://ta-lib.org/install/
```

## Shared Utility Foundation (Read These First!)

All tools depend on these core utilities in `tools/utils/`:

### 1. `exchange.py` - CCXT Client with Retry Logic
- **Shared instance**: `EXCHANGE = ccxt.gate({'enableRateLimit': True})`
- **Retry pattern**: `retry_on_error()` with exponential backoff (3 retries, 1s initial delay)
- **Key functions**: `fetch_ohlcv_cached()`, `fetch_ticker()`, `validate_timeframe()`, `validate_pair()`
- **Always use these wrappers** - never create raw CCXT client instances

### 2. `cache.py` - TTL-Based In-Memory Cache
- **Decorator**: `@cached(ttl=CACHE_TTL_SECONDS, prefix="key_prefix")`
- **Cache keys**: Generated via `cache_key(prefix, *args, **kwargs)`
- **Usage pattern**: Applied to expensive API calls (OHLCV fetches, indicator calculations)
- **Global instance**: Access via `get_cache()` for manual invalidation

### 3. `constants.py` - Shared Configuration
- Indicator periods: `RSI_PERIOD=14`, `MACD_FAST=12`, `MACD_SLOW=26`, `MACD_SIGNAL=9`
- Data limits: `DEFAULT_OHLCV_LIMIT=200`, `MAX_OHLCV_LIMIT=1000`
- Timeframes: `VALID_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']`
- Cache config: `CACHE_TTL_SECONDS=60`

### 4. `formatters.py` - Consistent Output Formatting
- `format_timestamp(dt)` → "YYYY-MM-DD HH:MM:SS UTC"
- `format_price(price, decimals=6)` → "1,234.567890"
- `format_percentage(value, decimals=2, include_sign=True)` → "+5.32%"
- `get_rsi_status(rsi_value)` → "Overbought" / "Oversold" / "Neutral"

### 5. `helpers.py` - Shared TA Calculations
- Moving averages: `sma()`, `ema()`, `wma()`, `hma()`, `vwma()`
- Indicators: `rsi_calc()`, `macd_calc()`, `bollinger_bands()`, `stochastic()`
- **DRY principle**: Never reimplement these calculations in tools

## Tool Development Pattern

**Standard Agno tool structure** (see `tools/market/prices.py` as canonical example):

```python
def get_crypto_price(coin: str, **kwargs) -> str:
    """
    Fetch REAL-TIME price data of a SINGLE cryptocurrency from Gate.
    
    Args:
        coin: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'XRP')
        
    Returns:
        Formatted price analysis string with real-time data
    """
    print(f"Tool 'get_crypto_price' was called with coin: {coin}!")
    
    # 1. Validation
    if not coin or not coin.strip():
        return "❌ Error: Please provide a valid cryptocurrency symbol..."
    
    coin_upper = coin.upper().strip()
    trading_pair = f"{coin_upper}/USDT"
    
    # 2. Fetch data using shared utility
    ticker, error = fetch_ticker(trading_pair)
    if error:
        return f"{error}\n\nReasoning: Failed to fetch ticker data..."
    
    # 3. Extract and validate numeric values
    price = float(ticker.get('last'))
    change_24h = float(ticker.get('change', 0.0))
    
    # 4. Format response using shared formatters
    response = f"""📊 {coin_upper} Price Analysis (Gate)
🕐 Data Fetched: {format_timestamp()} (Real-Time)

💰 Current Price: ${format_price(price, 2)} USDT

📈 24-Hour Performance:
   • Change: ${change_24h:+,.2f} ({format_percentage(change_percent_24h)})"""
    
    return response
```

**Key patterns**:
- **Print debug statements**: `print(f"Tool 'tool_name' was called with ...")`
- **Input validation first**: Return clear error messages with reasoning
- **Use shared utilities**: `fetch_ticker()`, `fetch_ohlcv_cached()`, not raw CCXT
- **Format all outputs**: Use `formatters.py` for consistency
- **Return strings**: Agno tools return formatted strings, not dicts/objects
- **Include reasoning**: Add `\n\nReasoning: ...` sections in error messages

## Agent Configuration

**Location**: `agents/cryage.py`

```python
from agno.agent import Agent
from agno.models.ollama import Ollama
from config.settings import MODEL_ID, AGENT_DESCRIPTION

def create_agent() -> Agent:
    return Agent(
        name="Cryage",
        model=Ollama(id=MODEL_ID),
        description=AGENT_DESCRIPTION,
        tools=[get_crypto_price, get_multi_prices, ...]
    )
```

**Adding new tools**:
1. Implement tool function in appropriate domain folder (`tools/market/`, `tools/indicators/`, etc.)
2. Import in `agents/cryage.py`
3. Add to `tools=[]` list

**Model config**: `config/settings.py` → `MODEL_ID = "hf.co/unsloth/granite-4.0-h-tiny-GGUF:IQ4_NL"`

## Domain Organization

Tools are organized by domain in `tools/`:

- **`market/`**: Real-time data (`prices.py`, `depth.py`, `flow.py`)
- **`indicators/`**: Technical indicators (`moving_averages.py`, `momentum.py`, `pivots.py`, `support_resistance.py`, `volume.py`)
- **`analysis/`**: Higher-level analysis (`forecast.py`, `ta_summary.py`)
- **`alerts/`**: Price alert management (`price_alerts.py`)
- **`portfolio/`**: Portfolio operations (`simulate.py`)
- **`utils/`**: Shared utilities (see above)

**Naming convention**: Tools use descriptive function names like `get_crypto_price()`, `get_rsi()`, `set_price_alert()`

## Development Workflow

### Running the Server
```bash
# Method 1: Direct uvicorn (recommended for dev)
uvicorn main:app --reload

# Method 2: Via main.py
python main.py
```

Server starts on `http://localhost:8000`

### Testing Patterns
See `tests/test_backend.py` for examples:
- Test imports from `tools.utils.*`
- Test helper functions with sample data
- Unit tests for individual calculations
- **Note**: No integration tests yet (planned with database layer)

### Build Order for New Features
1. **Start with utilities**: If adding new shared logic → `tools/utils/helpers.py`
2. **Implement tool**: Create in appropriate domain folder
3. **Register with agent**: Import and add to `agents/cryage.py` tools list
4. **Test**: Add unit test in `tests/`

## Important Conventions

### Error Handling
- **Validate inputs early**: Check for None, empty strings, invalid formats
- **Use error tuples**: Functions return `(result, error_msg)` or `(None, error_msg)`
- **Include reasoning**: Error messages explain what went wrong and why

### Caching Strategy
- **OHLCV data**: Cached for 60s (configurable via `CACHE_TTL_SECONDS`)
- **Indicators**: Calculated on cached OHLCV data (implicit caching)
- **Prices**: NOT cached (real-time requirement per `AGENT_DESCRIPTION`)

### Real-Time Data Emphasis
The agent description in `config/settings.py` emphasizes **ALWAYS fetch FRESH, REAL-TIME data**. While caching exists for performance, the agent's prompt instructs it to call tools for every query (no assumption of cached responses).

### Code Style
- Type hints for function parameters
- Docstrings with Args/Returns sections
- **Print debug statements** in tool functions for observability
- Emoji prefixes in formatted outputs (📊, 💰, 📈, ⚠️, ❌)

## Future Architecture (In Progress)

Documentation in `docs/` describes planned expansion:
- **Services layer**: `services/market_service.py`, `services/indicator_service.py`, etc.
- **Repository pattern**: `database/postgres/repositories/`, `database/questdb/repositories/`
- **Data pipelines**: `pipelines/` for background OHLCV ingestion and indicator calculation
- **API routes**: `api/v1/` for REST endpoints separate from Agno tools
- **WebSocket**: `api/websocket.py` for real-time streaming

**Current state**: Direct tool → CCXT pattern. Services/repositories not yet implemented.

## Key Files to Reference

When implementing new features, always check:
- `tools/market/prices.py` - Canonical tool example
- `tools/utils/exchange.py` - API call patterns
- `tools/utils/helpers.py` - Shared calculation logic
- `agents/cryage.py` - Tool registration
- `docs/ARCHITECTURE_SUMMARY.md` - High-level design
- `docs/QUICK_START_CHECKLIST.md` - Build order and setup

## Common Pitfalls

1. **Forgot TA-Lib system install**: `pip install ta-lib` will fail without system library
2. **Creating new CCXT client**: Always use shared `EXCHANGE` instance from `exchange.py`
3. **Reimplementing calculations**: Check `helpers.py` first before writing RSI/EMA/etc.
4. **Returning dicts from tools**: Agno tools must return formatted strings
5. **Inconsistent formatting**: Use `formatters.py` functions for dates/prices/percentages
6. **Skipping validation**: Always validate inputs before API calls
