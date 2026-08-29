"""
ATHENA Trade Journal & Explainability Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .decision import TradingDecision
from .order import Fill, OrderResponse
from .risk import RiskCheckResult


class TradeJournalEntry(BaseModel):
    trade_id: str
    symbol: str
    action: str  # BUY / SELL
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    shares: float
    total_cost: float
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    status: str = "OPEN"  # OPEN, CLOSED
    regime_at_entry: str
    decision_snapshot: TradingDecision
    risk_check_snapshot: RiskCheckResult
    order_fills: List[Fill] = Field(default_factory=list)
    confidence_at_entry: float
    predicted_return: float
    actual_return: Optional[float] = None
    prediction_error: Optional[float] = None
    explainability_report_markdown: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExplainabilityReport(BaseModel):
    trade_id: str
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision: str
    confidence_pct: float
    regime: str
    supporting_agents: List[str]
    opposing_agents: List[str]
    strongest_evidence: List[str]
    weakest_evidence: List[str]
    risk_assessment: str
    position_sizing_rationale: str
    stop_loss_rationale: str
    take_profit_rationale: str
    expected_return_pct: float
    expected_drawdown_pct: float
    alternative_scenarios: List[str]
    why_trade_approved: str
    rendered_markdown: str
