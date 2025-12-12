from agno.agent import Agent
from agno.models.ollama import Ollama

from config.settings import MODEL_ID, AGENT_DESCRIPTION
from tools.market.prices import get_crypto_price, get_multi_prices
from tools.market.depth import get_orderbook, get_recent_trades
from tools.market.flow import get_order_flow
from tools.market.killzones import get_ict_killzones
from tools.indicators.moving_averages import get_sma, get_ema_set
from tools.indicators.momentum import get_rsi, get_macd
from tools.indicators.pivots import get_pivot_points
from tools.indicators.support_resistance import get_support_resistance
from tools.indicators.volume import get_volume_profile
from tools.analysis.forecast import get_forecast
from tools.analysis.ta_summary import get_ta_summary
from tools.portfolio.simulate import simulate_portfolio_value
from tools.alerts.price_alerts import set_price_alert, list_alerts, remove_alert, check_alerts


def create_agent() -> Agent:
    return Agent(
        name="Cryage",
        model=Ollama(id=MODEL_ID),
        description=AGENT_DESCRIPTION,
        tools=[
            get_crypto_price,
            get_multi_prices,
            get_orderbook,
            get_recent_trades,
            get_ict_killzones,
            get_sma,
            get_ema_set,
            get_rsi,
            get_macd,
            simulate_portfolio_value,
            get_pivot_points,
            get_support_resistance,
            get_forecast,
            get_ta_summary,
            get_volume_profile,
            get_order_flow,
            set_price_alert,
            list_alerts,
            remove_alert,
            check_alerts,
        ],
    )
