"""
ATHENA Order & Deterministic Execution Schemas
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderStatus(str, Enum):
    PENDING_RISK = "PENDING_RISK"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ExecutionMode(str, Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"


class OrderRequest(BaseModel):
    client_order_id: str
    decision_id: Optional[str] = None
    symbol: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    quantity: float = Field(gt=0.0)
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    execution_mode: ExecutionMode = ExecutionMode.PAPER
    tag: Optional[str] = "ATHENA_AUTONOMOUS"


class Fill(BaseModel):
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fee: float = 0.0
    slippage_bps: float = 0.0
    liquidity: str = "TAKER"  # MAKER / TAKER


class OrderResponse(BaseModel):
    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    filled_quantity: float = 0.0
    remaining_quantity: float
    average_fill_price: Optional[float] = None
    status: OrderStatus = OrderStatus.SUBMITTED
    execution_mode: ExecutionMode = ExecutionMode.PAPER
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    fills: List[Fill] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    latency_ms: int = 0
