"""
ATHENA Broker Adapter Protocol & Interfaces
"""

from typing import Dict, List, Optional, Protocol
from packages.schemas.order import OrderRequest, OrderResponse
from packages.schemas.portfolio import Position


class Broker(Protocol):
    """Universal protocol for broker integration adapters."""

    async def submit_order(self, request: OrderRequest) -> OrderResponse: ...
    async def cancel_order(self, order_id: str) -> bool: ...
    async def get_order(self, order_id: str) -> Optional[OrderResponse]: ...
    async def get_positions(self) -> Dict[str, Position]: ...
    async def get_account_balance(self) -> float: ...
