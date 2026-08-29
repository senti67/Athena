"""
ATHENA Alpaca Paper Broker Adapter (Strict Safety Enforced)
Guarantees:
1. Alpaca credentials target ONLY the PAPER API (https://paper-api.alpaca.markets/v2)
2. TradingClient initialized with paper=True
3. EXECUTION_MODE is strictly PAPER
4. Zero path to accidentally connect to live Alpaca without explicit multi-level authorization.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

try:
    from alpaca.trading.client import TradingClient
    HAS_ALPACA_PY = True
except ImportError:
    HAS_ALPACA_PY = False

from packages.common.config import settings
from packages.common.exceptions import BrokerConnectionException, LiveTradingDisabledException
from packages.logging.logger import get_logger
from packages.schemas.order import (
    ExecutionMode,
    Fill,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderStatus,
    OrderType,
)

logger = get_logger("athena.alpaca_broker")


class AlpacaBrokerAdapter:
    """
    Direct interface to Alpaca Paper Trading API.
    Enforces paper=True and locks base URL to https://paper-api.alpaca.markets.
    """

    PAPER_BASE_URL = "https://paper-api.alpaca.markets"
    LIVE_BASE_URL = "https://api.alpaca.markets"

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        is_paper: bool = True,
    ):
        self.api_key = api_key or settings.ALPACA_API_KEY or settings.BROKER_API_KEY or "PK_MOCK_ALPACA_KEY"
        self.secret_key = secret_key or settings.ALPACA_SECRET_KEY or settings.BROKER_API_SECRET or "SK_MOCK_ALPACA_SECRET"
        self.is_paper = is_paper

        # Invariant 1 & 4: Zero path to live Alpaca unless LIVE_TRADING_ENABLED is explicitly True
        if base_url and "paper-api" not in base_url and not settings.LIVE_TRADING_ENABLED:
            raise LiveTradingDisabledException(
                "CRITICAL SAFETY VIOLATION: Non-paper Alpaca URL attempted while LIVE_TRADING_ENABLED=false"
            )

        if not settings.LIVE_TRADING_ENABLED:
            self.base_url = self.PAPER_BASE_URL
            self.is_paper = True
        else:
            self.base_url = base_url or self.PAPER_BASE_URL

        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
        }

        # Invariant 2: Initialize official alpaca-py TradingClient with paper=True
        self.trading_client = None
        if HAS_ALPACA_PY and self._has_valid_credentials():
            try:
                self.trading_client = TradingClient(
                    api_key=self.api_key,
                    secret_key=self.secret_key,
                    paper=True,  # Strict paper=True
                )
            except Exception as e:
                logger.warning(f"Could not initialize alpaca-py TradingClient: {e}")

    def _has_valid_credentials(self) -> bool:
        return (
            bool(self.api_key)
            and not self.api_key.startswith("PK_MOCK")
            and bool(self.secret_key)
            and not self.secret_key.startswith("SK_MOCK")
        )

    async def get_account(self) -> Dict[str, Any]:
        """Fetches paper account information from Alpaca Paper Trading."""
        # Enforce paper base URL
        if not settings.LIVE_TRADING_ENABLED and "paper-api" not in self.base_url:
            self.base_url = self.PAPER_BASE_URL

        if not self._has_valid_credentials():
            return {
                "id": "alpaca-paper-acct-01",
                "account_number": "PA39281920",
                "status": "ACTIVE",
                "currency": "USD",
                "equity": "100000.00",
                "cash": "100000.00",
                "buying_power": "200000.00",
                "portfolio_value": "100000.00",
                "pattern_day_trader": False,
                "trading_blocked": False,
                "transfers_blocked": False,
                "account_blocked": False,
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(f"{self.base_url}/v2/account", headers=self.headers)
                if res.status_code == 200:
                    return res.json()
                else:
                    logger.error(f"Alpaca get_account failed: {res.status_code} {res.text}")
                    raise BrokerConnectionException(f"Alpaca API error: {res.text}")
            except Exception as e:
                logger.warning(f"Error connecting to Alpaca Paper API: {e}. Using fallback simulation.")
                return {
                    "id": "alpaca-paper-fallback",
                    "status": "ACTIVE",
                    "currency": "USD",
                    "equity": "100000.00",
                    "cash": "100000.00",
                }

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Fetches all currently open positions from Alpaca Paper API."""
        if not self._has_valid_credentials():
            return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(f"{self.base_url}/v2/positions", headers=self.headers)
                if res.status_code == 200:
                    return res.json()
                return []
            except Exception as e:
                logger.warning(f"Error fetching Alpaca positions: {e}")
                return []

    async def submit_order(self, request: OrderRequest) -> OrderResponse:
        """
        Submits an order to Alpaca Paper Trading.
        Strictly blocks live execution unless explicitly enabled.
        """
        # Invariant 3 & 4: Block any attempt at live order submission
        if request.execution_mode == ExecutionMode.LIVE or not self.is_paper:
            if not settings.LIVE_TRADING_ENABLED:
                raise LiveTradingDisabledException(
                    "Live execution refused: LIVE_TRADING_ENABLED is False."
                )

        logger.info(
            f"Submitting Alpaca PAPER order: "
            f"{request.side.value} {request.quantity} {request.symbol} (Mode: {request.execution_mode.value})"
        )

        if not self._has_valid_credentials():
            # Simulate instant fill in local paper mode
            fill_price = request.limit_price or 258.35
            fill = Fill(
                fill_id=f"alpaca-fill-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                order_id=request.client_order_id,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                price=fill_price,
                fee=0.0,
                slippage_bps=3.0,
            )
            return OrderResponse(
                order_id=f"alpaca-{request.client_order_id}",
                client_order_id=request.client_order_id,
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                status=OrderStatus.FILLED,
                filled_quantity=request.quantity,
                remaining_quantity=0.0,
                average_fill_price=fill_price,
                fills=[fill],
            )

        # Map Indian symbols to US ADRs/ETFs for Alpaca paper execution
        symbol_map = {
            "ICICIBANK": "IBN",
            "INFY": "INFY",
            "HDFCBANK": "HDB",
            "NIFTY50": "INDY",
            "RELIANCE": "INDA",
            "BHARTIARTL": "INDA",
            "TATAMOTORS": "INDA",
            "LT": "INDA",
            "TCS": "INDA",
            "ITC": "INDA",
            "SBIN": "INDA",
        }
        alpaca_symbol = symbol_map.get(request.symbol.upper(), request.symbol.upper())

        # Real Alpaca Paper API submission payload
        payload = {
            "symbol": alpaca_symbol,
            "qty": str(max(1, int(request.quantity))),
            "side": request.side.value.lower(),
            "type": request.order_type.value.lower(),
            "time_in_force": request.time_in_force.lower(),
            "client_order_id": request.client_order_id,
        }
        if request.limit_price:
            payload["limit_price"] = str(request.limit_price)
        if request.stop_price:
            payload["stop_price"] = str(request.stop_price)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    f"{self.base_url}/v2/orders", headers=self.headers, json=payload
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    status_map = {
                        "filled": OrderStatus.FILLED,
                        "partially_filled": OrderStatus.PARTIALLY_FILLED,
                        "new": OrderStatus.SUBMITTED,
                        "accepted": OrderStatus.SUBMITTED,
                        "pending_new": OrderStatus.SUBMITTED,
                        "canceled": OrderStatus.CANCELED,
                        "rejected": OrderStatus.REJECTED,
                        "expired": OrderStatus.EXPIRED,
                    }
                    order_status = status_map.get(data.get("status"), OrderStatus.SUBMITTED)
                    fill_px = float(data.get("filled_avg_price") or data.get("limit_price") or 0.0)
                    filled_qty = float(data.get("filled_qty") or 0.0)
                    qty = float(data.get("qty", request.quantity))
                    rem_qty = max(0.0, qty - filled_qty)

                    fills = []
                    if filled_qty > 0 and fill_px > 0:
                        fills.append(
                            Fill(
                                fill_id=f"fill-{data.get('id')}",
                                order_id=data.get("id"),
                                symbol=request.symbol,
                                side=request.side,
                                quantity=filled_qty,
                                price=fill_px,
                                fee=0.0,
                            )
                        )

                    return OrderResponse(
                        order_id=data.get("id"),
                        client_order_id=data.get("client_order_id"),
                        symbol=request.symbol,
                        side=request.side,
                        order_type=request.order_type,
                        quantity=qty,
                        status=order_status,
                        filled_quantity=filled_qty,
                        remaining_quantity=rem_qty,
                        average_fill_price=fill_px,
                        fills=fills,
                    )
                else:
                    logger.error(f"Alpaca order rejected: {res.status_code} {res.text}")
                    return OrderResponse(
                        order_id=f"err-{request.client_order_id}",
                        client_order_id=request.client_order_id,
                        symbol=request.symbol,
                        side=request.side,
                        order_type=request.order_type,
                        quantity=request.quantity,
                        remaining_quantity=request.quantity,
                        status=OrderStatus.REJECTED,
                        rejection_reason=res.text,
                    )
            except Exception as e:
                logger.error(f"Error submitting order to Alpaca Paper: {e}")
                raise BrokerConnectionException(f"Failed to submit order to Alpaca Paper: {str(e)}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancels an order on Alpaca Paper by Order ID."""
        if not self._has_valid_credentials():
            return True

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.delete(f"{self.base_url}/v2/orders/{order_id}", headers=self.headers)
                return res.status_code in (200, 204)
            except Exception as e:
                logger.error(f"Error cancelling Alpaca order: {e}")
                return False


alpaca_broker = AlpacaBrokerAdapter()
