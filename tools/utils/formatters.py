"""
Formatting utilities for consistent output across tools.
"""
from datetime import datetime
from typing import Optional


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime to standard UTC string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')


def format_price(price: float, decimals: int = 6) -> str:
    """Format price with proper decimal places."""
    return f"{price:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2, include_sign: bool = True) -> str:
    """Format percentage value."""
    if include_sign:
        return f"{value:+.{decimals}f}%"
    return f"{value:.{decimals}f}%"


def format_volume(volume: float, decimals: int = 2) -> str:
    """Format volume with proper decimal places."""
    return f"{volume:,.{decimals}f}"


def get_rsi_status(rsi_value: float) -> str:
    """Get RSI status label."""
    if rsi_value >= 70:
        return 'Overbought'
    elif rsi_value <= 30:
        return 'Oversold'
    return 'Neutral'


def get_stoch_status(stoch_value: float) -> str:
    """Get Stochastic status label."""
    if stoch_value >= 80:
        return 'Overbought'
    elif stoch_value <= 20:
        return 'Oversold'
    return 'Neutral'


def get_macd_momentum(macd: float, signal: float) -> str:
    """Get MACD momentum label."""
    if macd > signal:
        return 'Bullish'
    elif macd < signal:
        return 'Bearish'
    return 'Flat'


def get_trend_label(slope: float, threshold: float = 0.0001) -> str:
    """Get trend label from slope value."""
    if slope > threshold:
        return 'Uptrend'
    elif slope < -threshold:
        return 'Downtrend'
    return 'Flat'


def format_error(coin: str, error: Exception, pair: Optional[str] = None) -> str:
    """Format error message consistently."""
    if pair is None:
        pair = f"{coin.upper()}/USDT"
    return f"❌ Error fetching data for {pair}: {str(error)}"


def format_no_data(coin: str, pair: Optional[str] = None) -> str:
    """Format no data message consistently."""
    if pair is None:
        pair = f"{coin.upper()}/USDT"
    return f"⚠️ No data available for {pair}"


def format_insufficient_data(coin: str, required: int, available: int) -> str:
    """Format insufficient data message."""
    pair = f"{coin.upper()}/USDT"
    return f"⚠️ Insufficient data for {pair}. Required: {required}, Available: {available}"


def build_header(title: str, pair: str, timeframe: Optional[str] = None) -> str:
    """Build formatted header for output."""
    ts = format_timestamp()
    header = f"🕐 {ts} {title} {pair}"
    if timeframe:
        header += f" | Timeframe: {timeframe}"
    return header


def format_confidence_message(r2: float) -> str:
    """Format confidence message based on R² value."""
    if r2 >= 0.9:
        return "✅ High confidence forecast (R² ≥ 0.9)"
    elif r2 >= 0.7:
        return "⚠️ Moderate confidence forecast (R² ≥ 0.7)"
    return "⚠️ Low confidence forecast (R² < 0.7) - use with caution"
