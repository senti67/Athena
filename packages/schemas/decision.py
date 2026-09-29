"""
ATHENA Quantitative Decision Engine Schemas
Defines deterministic TradingDecisions with full mathematical explainability, expected edge, and risk metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


class AlternativeScenario(BaseModel):
    name: str  # e.g., "Bearish Macro Escalation", "Earnings Miss"
    trigger_condition: str
    probability: float = 0.20
    mitigation_action: str  # e.g., "Tighten stop loss to $215", "Exit 50% position"


class TradingDecision(BaseModel):
    id: str = Field(default="DEC-DEFAULT-001", description="Unique Decision UUID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str
    action: ActionType
    confidence: float = Field(ge=0.0, le=1.0, description="Ensemble confidence")
    calibrated_probability: float = Field(
        ge=0.0, le=1.0, default=0.55, description="Calibrated win probability"
    )
    current_price: float
    target_weight: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of portfolio capital"
    )
    suggested_shares: int = 0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    expected_edge: float = Field(default=0.0, description="Estimated directional edge (expected return)")
    expected_value: float = Field(default=0.0, description="P(win)*AvgWin - P(loss)*AvgLoss")
    expected_return_pct: float = 0.0
    expected_drawdown_pct: float = 0.0
    risk_reward_ratio: float = 2.0
    holding_period: str = "5D"
    regime: str = "TRENDING_BULL"
    regime_compatibility: float = 1.0
    data_quality_score: float = 1.0
    triggering_strategy: Optional[str] = None
    feature_group_scores: Dict[str, float] = Field(default_factory=dict)
    strategy_scores: Dict[str, float] = Field(default_factory=dict)
    debate_agreement_score: float = 0.80
    supporting_agents: List[str] = Field(default_factory=list)
    opposing_agents: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="", alias="reason")
    alternative_scenarios: List[AlternativeScenario] = Field(default_factory=list)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    validation_status: str = "VALIDATED"  # VALIDATED or REJECTED
    validation_reasons: List[str] = Field(default_factory=list)
    execution_mode: str = "PAPER"

    class Config:
        populate_by_name = True

    @property
    def reason(self) -> str:
        return self.reasoning


# Compatibility alias
DecisionProposal = TradingDecision
