"""
ATHENA Portfolio & Capital Allocation Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class OptimizationObjective(str, Enum):
    MAX_SHARPE = "MAX_SHARPE"
    MIN_VOLATILITY = "MIN_VOLATILITY"
    RISK_PARITY = "RISK_PARITY"
    MIN_CVAR = "MIN_CVAR"
    KELLY_CRITERION = "KELLY_CRITERION"
    VOLATILITY_TARGETING = "VOLATILITY_TARGETING"


class Position(BaseModel):
    symbol: str
    asset_class: str = "EQUITY"
    sector: str = "Technology"
    shares: float
    average_entry_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    portfolio_weight: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PortfolioState(BaseModel):
    account_id: str = "ATHENA_MASTER_PORTFOLIO"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    nav: float = 100000.0
    cash: float = 100000.0
    positions: Dict[str, Position] = Field(default_factory=dict)
    total_positions_count: int = 0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    leverage: float = 0.0
    daily_realized_pnl: float = 0.0
    daily_unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    total_return_pct: float = 0.0
    sector_allocations: Dict[str, float] = Field(default_factory=dict)


class TargetAllocation(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE
    target_weights: Dict[str, float] = Field(default_factory=dict)
    expected_annual_return: float = 0.18
    expected_annual_volatility: float = 0.12
    portfolio_sharpe_ratio: float = 1.50
    portfolio_cvar_95: float = 0.025
    rebalance_orders_needed: List[Dict[str, float]] = Field(default_factory=list)
