"""
Constants used across trading tools.
"""

# Technical Indicator Periods
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_SMOOTH_K = 3

# Moving Average Periods
SMA_SHORT = 20
SMA_MEDIUM = 50
SMA_LONG = 200
EMA_FAST = 9
EMA_MEDIUM = 21
EMA_SLOW = 55

# Bollinger Bands
BB_PERIOD = 20
BB_STD_DEV = 2

# RSI Thresholds
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Stochastic Thresholds
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20

# Data Limits
DEFAULT_OHLCV_LIMIT = 200
MIN_DATA_POINTS = 50
MAX_OHLCV_LIMIT = 1000

# Timeframes
VALID_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']

# Alert Conditions
VALID_ALERT_CONDITIONS = ['above', 'below', 'crosses_above', 'crosses_below']

# Cache Settings
CACHE_TTL_SECONDS = 60  # 1 minute cache for market data
CACHE_TTL_ALERTS = 300  # 5 minutes cache for alerts

# Formatting
PRICE_DECIMALS = 6
PERCENTAGE_DECIMALS = 2
VOLUME_DECIMALS = 2
