"""
ATHENA Deterministic Execution Router (Alpaca Paper Trading Integration)
Coordinates Decision -> Risk Veto -> Order Creation -> Broker Dispatch -> Telegram Notification -> Portfolio Update.
"""

import uuid
from typing import Optional
from packages.common.config import settings
from packages.common.exceptions import RiskVetoException
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.decision import ActionType, TradingDecision
from packages.schemas.events import Event, EventType
from packages.schemas.order import (
    ExecutionMode,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderType,
)
from packages.schemas.risk import RiskCheckResult
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager
from .alpaca_broker import alpaca_broker
from .live_broker import live_broker
from .paper_broker import paper_broker

logger = get_logger("athena.execution_router")


class ExecutionRouter:
    """Deterministic, safety-audited order execution pipeline with Alpaca & Telegram support."""

    def __init__(self):
        self.alpaca_broker = alpaca_broker
        self.paper_broker = paper_broker
        self.live_broker = live_broker

    async def execute_trade(
        self,
        decision: TradingDecision,
        risk_check: RiskCheckResult,
        mode: ExecutionMode = ExecutionMode.PAPER,
    ) -> Optional[OrderResponse]:
        # 0. Master Emergency Kill Switch & Analysis-Only Check
        if settings.CIRCUIT_BREAKER_TRIGGERED or settings.EXECUTION_MODE == "ANALYSIS_ONLY":
            logger.warning("Execution Router: Master Kill Switch / ANALYSIS_ONLY mode is active. Order blocked.")
            return None

        # 1. Non-bypassable Risk Veto Verification
        if not risk_check.approved:
            logger.warning(
                f"Execution Router blocked order for {decision.symbol}: {risk_check.veto_reason}"
            )
            await event_bus.publish(
                Event(
                    event_type=EventType.RISK_REJECTED,
                    payload={"decision_id": decision.id, "reason": risk_check.veto_reason},
                )
            )
            await telegram_notifier.notify_risk_veto(decision.symbol, risk_check.veto_reason)
            raise RiskVetoException(f"Order vetoed by Risk Management: {risk_check.veto_reason}")

        if decision.action not in (ActionType.BUY, ActionType.SELL) or risk_check.max_approved_shares <= 0:
            logger.info(f"No execution needed for action {decision.action.value}")
            return None

        # 2. Construct Strongly-Typed Order Request
        client_order_id = f"ATHENA-{decision.symbol}-{uuid.uuid4().hex[:8].upper()}"
        side = OrderSide.BUY if decision.action == ActionType.BUY else OrderSide.SELL

        order_request = OrderRequest(
            client_order_id=client_order_id,
            decision_id=decision.id,
            symbol=decision.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=float(risk_check.max_approved_shares),
            execution_mode=mode,
        )

        # 3. Publish Order Submission Event
        await event_bus.publish(
            Event(
                event_type=EventType.ORDER_SUBMITTED,
                payload={
                    "client_order_id": client_order_id,
                    "symbol": decision.symbol,
                    "side": side.value,
                    "quantity": risk_check.max_approved_shares,
                    "mode": mode.value,
                },
            )
        )

        # 4. Enforce Live $200k Alpaca Buying Power Floor Check
        if side == OrderSide.BUY and (settings.BROKER_PROVIDER == "alpaca" or mode == ExecutionMode.PAPER):
            acct = await self.alpaca_broker.get_account()
            live_bp = float(acct.get("buying_power", 400000.0))
            order_cost = float(risk_check.max_approved_shares) * decision.current_price
            # Alpaca margin multiplier reservation
            projected_bp = live_bp - (order_cost * 4.0)

            if live_bp < settings.MIN_BUYING_POWER_RESERVE or projected_bp < settings.MIN_BUYING_POWER_RESERVE:
                veto_msg = (
                    f"Mandatory $200,000.00 Buying Power Floor active. "
                    f"Current Alpaca BP is ${live_bp:,.2f}. Order rejected to protect $200k minimum reserve."
                )
                logger.warning(veto_msg)
                await telegram_notifier.notify_risk_veto(decision.symbol, veto_msg)
                raise RiskVetoException(veto_msg)

        # 5. Dispatch to Chosen Broker Adapter (Alpaca Paper / Alpaca Live / Internal)
        if settings.BROKER_PROVIDER == "alpaca" or mode == ExecutionMode.PAPER:
            order_response = await self.alpaca_broker.submit_order(order_request)
        elif mode == ExecutionMode.LIVE:
            order_response = await self.live_broker.submit_order(order_request)
        else:
            order_response = await self.paper_broker.submit_order(order_request)

        # 5. Dispatch Telegram Trade Notification
        await telegram_notifier.notify_order_submitted(
            symbol=decision.symbol,
            action=decision.action.value,
            quantity=float(risk_check.max_approved_shares),
            price=decision.current_price,
            order_id=order_response.order_id,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            confidence=decision.confidence,
        )

        # 6. Process Fills and Update Portfolio
        for fill in order_response.fills:
            portfolio_manager.update_position_from_fill(
                symbol=fill.symbol,
                side=fill.side.value,
                shares=fill.quantity,
                price=fill.price,
                fee=fill.fee,
            )

            await event_bus.publish(
                Event(
                    event_type=EventType.ORDER_FILLED,
                    payload={
                        "order_id": order_response.order_id,
                        "symbol": fill.symbol,
                        "side": fill.side.value,
                        "quantity": fill.quantity,
                        "price": fill.price,
                        "fee": fill.fee,
                        "slippage_bps": fill.slippage_bps,
                    },
                )
            )

        return order_response


execution_router = ExecutionRouter()
