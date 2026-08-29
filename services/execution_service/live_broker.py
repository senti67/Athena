"""
ATHENA Live Broker Interface Adapter
Guarantees strict safety bounds and enforces the master kill-switch rule.
"""

from typing import Dict, Optional
from packages.common.config import settings
from packages.common.exceptions import LiveTradingDisabledException
from packages.logging.logger import get_logger
from packages.schemas.order import OrderRequest, OrderResponse
from packages.schemas.portfolio import Position

logger = get_logger("athena.live_broker")


class LiveBrokerAdapter:
    """
    Live broker gateway.
    CRITICAL RULE 3: Refuses live orders unless LIVE_TRADING_ENABLED=true in config.
    """

    def __init__(self):
        self.is_enabled = settings.LIVE_TRADING_ENABLED

    async def submit_order(self, request: OrderRequest) -> OrderResponse:
        if not self.is_enabled:
            error_msg = (
                "CRITICAL SECURITY REJECTION: Live trading is disabled by default "
                "(LIVE_TRADING_ENABLED=false). Order refused."
            )
            logger.critical(error_msg)
            raise LiveTradingDisabledException(error_msg)

        # Real broker submission (e.g. Alpaca, Interactive Brokers) would be called here
        raise NotImplementedError("Live broker gateway requires explicit production authentication keys.")

    async def cancel_order(self, order_id: str) -> bool:
        if not self.is_enabled:
            return False
        return True

    async def get_order(self, order_id: str) -> Optional[OrderResponse]:
        return None

    async def get_positions(self) -> Dict[str, Position]:
        return {}

    async def get_account_balance(self) -> float:
        return 0.0


live_broker = LiveBrokerAdapter()
