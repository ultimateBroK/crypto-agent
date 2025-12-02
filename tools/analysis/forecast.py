from datetime import datetime
import numpy as np
from typing import Optional
from tools.utils.exchange import fetch_ohlcv
from tools.utils.nlp import resolve_timeframe


def get_forecast(coin: str, timeframe: Optional[str] = None, train_len: int = 100, forecast_len: int = 10, **kwargs):
    """Linear regression forecast for price movement."""
    pair = f"{coin.upper().strip()}/USDT"
    # Resolve timeframe from kwargs/prompt, honoring natural-language hints
    timeframe, tf_reason = resolve_timeframe(timeframe, return_reason=True, **kwargs)

    ohlcv, error = fetch_ohlcv(pair, timeframe=timeframe, limit=train_len + 10)
    if error:
        return error
    
    if len(ohlcv) < train_len:
        return f"⚠️ Not enough data for {pair}"
    
    closes = np.array([x[4] for x in ohlcv[-train_len:]])
    X = np.arange(len(closes)).reshape(-1, 1)
    
    X_mean = X.mean()
    y_mean = closes.mean()
    num = ((X.flatten() - X_mean) * (closes - y_mean)).sum()
    denom = ((X.flatten() - X_mean) ** 2).sum()
    slope = num / denom if denom != 0 else 0
    intercept = y_mean - slope * X_mean
    
    future_X = np.arange(len(closes), len(closes) + forecast_len)
    forecast_vals = slope * future_X + intercept
    
    y_pred = slope * X.flatten() + intercept
    corr = np.corrcoef(closes, y_pred)[0, 1] if len(closes) > 1 else 0
    r2 = corr ** 2
    
    residuals = closes - y_pred
    std_dev = np.std(residuals)
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    current_price = closes[-1]
    forecast_end = forecast_vals[-1]
    change_pct = (forecast_end - current_price) / current_price * 100
    
    trend = "Uptrend" if slope > 0 else "Downtrend" if slope < 0 else "Flat"
    
    out = f"""🕐 {ts} Price Forecast {pair}
Timeframe: {timeframe} | Train: {train_len} bars | Forecast: {forecast_len} bars

Current Price: {current_price:.6f}
Forecast Price ({forecast_len} bars): {forecast_end:.6f}
Expected Change: {change_pct:+.2f}%

Model Statistics:
  Trend: {trend}
  Slope: {slope:.6f} per bar
  R (correlation): {corr:.3f}
  R² (quality): {r2:.3f}
  Std Dev: {std_dev:.6f}

Confidence Band:
  Upper: {forecast_end + 2*std_dev:.6f}
  Lower: {forecast_end - 2*std_dev:.6f}
"""
    
    if r2 >= 0.9:
        out += "\n✅ High confidence forecast (R² ≥ 0.9)"
    elif r2 >= 0.7:
        out += "\n⚠️ Moderate confidence forecast (R² ≥ 0.7)"
    else:
        out += "\n⚠️ Low confidence forecast (R² < 0.7) - use with caution"
    
    if tf_reason:
        out += f"\n⚠️ Note: {tf_reason}"
    return out


