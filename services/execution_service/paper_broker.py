"""
ATHENA Institutional Paper Trading Broker
Simulates execution latency, realistic market slippage, spread friction, and order fills.
"""

import asyncio
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.monitoring.metrics import metrics
from packages.schemas.order import (
    ExecutionMode,
    Fill,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderStatus,
)
from services.data_service.pipeline import data_pipeline

logger = get_logger("athena.paper_broker")


class PaperBroker:
    """Realistic simulation broker for zero-risk algorithm execution."""

    def __init__(self, starting_cash: float = 100000.0):
        self.cash = starting_cash
        self.orders: Dict[str, OrderResponse] = {}
        self.slippage_bps = settings.PAPER_SLIPPAGE_BPS
        self.commission_per_share = settings.PAPER_COMMISSION_PER_SHARE
        self.latency_ms = settings.PAPER_LATENCY_MS

    async def submit_order(self, request: OrderRequest) -> OrderResponse:
        order_id = str(uuid.uuid4())
        quote = await data_pipeline.get_realtime_quote(request.symbol)
        market_price = quote.price

        # 1. Simulate Network Latency
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000.0)

        # 2. Calculate Realistic Slippage & Fill Price
        slippage_pct = (self.slippage_bps / 10000.0) + random.uniform(0.0, 0.0004)
        if request.side == OrderSide.BUY:
            fill_price = round(market_price * (1.0 + slippage_pct), 2)
        else:
            fill_price = round(market_price * (1.0 - slippage_pct), 2)

        # 3. Calculate Commissions
        fee = round(request.quantity * self.commission_per_share, 2)
        fill_id = str(uuid.uuid4())

        fill = Fill(
            fill_id=fill_id,
            order_id=order_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=fill_price,
            timestamp=datetime.utcnow(),
            fee=fee,
            slippage_bps=round(slippage_pct * 10000.0, 2),
        )

        response = OrderResponse(
            order_id=order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            filled_quantity=request.quantity,
            remaining_quantity=0.0,
            average_fill_price=fill_price,
            status=OrderStatus.FILLED,
            execution_mode=ExecutionMode.PAPER,
            submitted_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            fills=[fill],
            latency_ms=self.latency_ms,
        )

        self.orders[order_id] = response
        metrics.record_order(request.symbol, request.side.value, "FILLED", "PAPER")
        metrics.record_fill(request.symbol, request.side.value)

        logger.info(
            f"[PAPER FILL] {request.side.value} {request.quantity} {request.symbol} @ ${fill_price:.2f} (slippage={slippage_pct*10000:.1f}bps, fee=${fee:.2f})"
        )
        return response

    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELED
            return True
        return False

    async def get_order(self, order_id: str) -> Optional[OrderResponse]:
        return self.orders.get(order_id)

    async def get_account_balance(self) -> float:
        return self.cash


paper_broker = PaperBroker()
