"""
Price alert management with improved storage and shared utilities.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from tools.utils.exchange import EXCHANGE, fetch_ticker
from tools.utils.formatters import format_timestamp, format_price
from tools.utils.constants import VALID_ALERT_CONDITIONS


ALERTS_FILE = Path(__file__).parent.parent.parent / "data" / "alerts.json"


def _load_alerts():
    if not ALERTS_FILE.exists():
        ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        with open(ALERTS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_alerts(alerts):
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)


def set_price_alert(coin: str, condition: str, price: float, message: str = "", **kwargs) -> str:
    """
    Set a price alert for a cryptocurrency.
    
    Args:
        coin: Cryptocurrency symbol
        condition: Alert condition (above, below, crosses_above, crosses_below)
        price: Target price
        message: Optional custom message
        
    Returns:
        Confirmation message
    """
    coin_upper = coin.upper().strip()
    
    if condition not in VALID_ALERT_CONDITIONS:
        return f"❌ Invalid condition. Use one of: {', '.join(VALID_ALERT_CONDITIONS)}"
    
    if price <= 0:
        return "❌ Price must be greater than 0"
    
    alerts = _load_alerts()
    alert_id = f"{coin_upper}_{condition}_{price}_{datetime.now().timestamp()}"
    alert_data = {
        'coin': coin_upper,
        'condition': condition,
        'price': price,
        'message': message or f"{coin_upper} price {condition} {price}",
        'created_at': datetime.utcnow().isoformat(),
        'triggered': False,
        'last_check_price': None
    }
    
    alerts[alert_id] = alert_data
    _save_alerts(alerts)
    
    ts = format_timestamp()
    return f"""✅ Price Alert Created
🕐 {ts}

Alert ID: {alert_id}
Coin: {coin_upper}/USDT
Condition: Price {condition} ${format_price(price, 2)}
Message: {alert_data['message']}

Use check_alerts() to monitor active alerts.
Use list_alerts() to see all alerts.
Use remove_alert(alert_id) to delete this alert.
"""


def list_alerts(coin: str = None, **kwargs):
    alerts = _load_alerts()
    if not alerts:
        return "📭 No active alerts"
    coin_filter = coin.upper().strip() if coin else None
    filtered_alerts = {
        aid: data for aid, data in alerts.items()
        if not coin_filter or data['coin'] == coin_filter
    }
    if not filtered_alerts:
        msg = f"📭 No active alerts for {coin_filter}" if coin_filter else "📭 No active alerts"
        return msg
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    out = f"🕐 {ts} Active Price Alerts\n"
    if coin_filter:
        out += f"Filtered by: {coin_filter}\n"
    out += f"Total: {len(filtered_alerts)} alert(s)\n\n"
    for alert_id, data in filtered_alerts.items():
        status = "✅ TRIGGERED" if data['triggered'] else "⏳ ACTIVE"
        out += f"{status} | {data['coin']}/USDT\n"
        out += f"  Condition: Price {data['condition']} ${data['price']:,.2f}\n"
        out += f"  Created: {data['created_at'][:19]}\n"
        if data['message']:
            out += f"  Message: {data['message']}\n"
        if data['last_check_price']:
            out += f"  Last Price: ${data['last_check_price']:,.2f}\n"
        out += f"  ID: {alert_id}\n\n"
    return out


def remove_alert(alert_id: str, **kwargs):
    alerts = _load_alerts()
    if alert_id not in alerts:
        return f"❌ Alert ID not found: {alert_id}\n\nUse list_alerts() to see available alerts."
    alert_data = alerts.pop(alert_id)
    _save_alerts(alerts)
    return f"""🗑️ Alert Removed
Coin: {alert_data['coin']}/USDT
Condition: Price {alert_data['condition']} ${alert_data['price']:,.2f}
ID: {alert_id}
"""


def check_alerts(coin: str = None, **kwargs) -> str:
    """
    Check all active alerts and trigger if conditions are met.
    
    Args:
        coin: Optional coin filter to check specific coin's alerts
        
    Returns:
        Alert check results with triggered and active alerts
    """
    alerts = _load_alerts()
    if not alerts:
        return "📭 No active alerts to check"
    
    coin_filter = coin.upper().strip() if coin else None
    filtered_alerts = {
        aid: data for aid, data in alerts.items()
        if not coin_filter or data['coin'] == coin_filter
    }
    
    if not filtered_alerts:
        msg = f"📭 No alerts to check for {coin_filter}" if coin_filter else "📭 No alerts to check"
        return msg
    
    triggered = []
    active = []
    errors = []
    
    for alert_id, data in filtered_alerts.items():
        pair = f"{data['coin']}/USDT"
        
        # Fetch current price using shared utility
        ticker_data, error = fetch_ticker(pair)
        if error:
            errors.append(f"{data['coin']}: {error}")
            continue
        
        current_price = ticker_data.get('last')
        if current_price is None:
            errors.append(f"{data['coin']}: Price unavailable")
            continue
        
        prev_price = data.get('last_check_price')
        data['last_check_price'] = current_price
        
        condition = data['condition']
        target = data['price']
        is_triggered = False
        
        # Check trigger conditions
        if condition == 'above' and current_price > target:
            is_triggered = True
        elif condition == 'below' and current_price < target:
            is_triggered = True
        elif condition == 'crosses_above' and prev_price and prev_price <= target < current_price:
            is_triggered = True
        elif condition == 'crosses_below' and prev_price and prev_price >= target > current_price:
            is_triggered = True
        
        if is_triggered and not data['triggered']:
            data['triggered'] = True
            triggered.append({
                'coin': data['coin'],
                'condition': condition,
                'target': target,
                'current': current_price,
                'message': data['message'],
                'id': alert_id
            })
        elif not data['triggered']:
            active.append({
                'coin': data['coin'],
                'condition': condition,
                'target': target,
                'current': current_price
            })
    
    # Update alerts with new check data
    alerts.update(filtered_alerts)
    _save_alerts(alerts)
    
    # Format output
    ts = format_timestamp()
    out = f"🕐 {ts} Alert Check Results\n\n"
    
    if triggered:
        out += f"🔔 TRIGGERED ALERTS ({len(triggered)}):\n"
        for t in triggered:
            out += f"\n  🚨 {t['coin']}/USDT\n"
            out += f"     Condition: Price {t['condition']} ${format_price(t['target'], 2)}\n"
            out += f"     Current Price: ${format_price(t['current'], 2)}\n"
            out += f"     Message: {t['message']}\n"
            out += f"     ID: {t['id']}\n"
        out += "\n"
    
    if active:
        out += f"⏳ ACTIVE ALERTS ({len(active)}):\n"
        for a in active:
            diff = ((a['current'] - a['target']) / a['target'] * 100)
            out += f"  • {a['coin']}: ${format_price(a['current'], 2)} (target {a['condition']} ${format_price(a['target'], 2)}, {diff:+.2f}%)\n"
        out += "\n"
    
    if errors:
        out += f"⚠️ ERRORS ({len(errors)}):\n"
        for err in errors:
            out += f"  • {err}\n"
    
    if not triggered and not errors:
        out += "✅ All alerts checked, no triggers at this time.\n"
    
    return out


