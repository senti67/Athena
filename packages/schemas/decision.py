"""
ATHENA Quantitative Decision Engine Schemas
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
    id: str = Field(description="Unique Decision UUID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str
    action: ActionType
    confidence: float = Field(ge=0.0, le=1.0, description="Ensemble confidence")
    calibrated_probability: float = Field(
        ge=0.0, le=1.0, default=0.70, description="Platt-calibrated win probability"
    )
    current_price: float
    target_weight: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Fraction of portfolio capital"
    )
    suggested_shares: int = 0
    stop_loss: float
    take_profit: float
    expected_return_pct: float = 0.05
    expected_drawdown_pct: float = 0.02
    risk_reward_ratio: float = 2.5
    holding_period: str = "5D"
    regime: str = "BULL"
    debate_agreement_score: float = 0.80
    supporting_agents: List[str] = Field(default_factory=list)
    opposing_agents: List[str] = Field(default_factory=list)
    reasoning: str
    alternative_scenarios: List[AlternativeScenario] = Field(default_factory=list)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    prompt_versions: Dict[str, str] = Field(default_factory=dict)
    validation_status: str = "VALIDATED"  # VALIDATED or REJECTED
    validation_reasons: List[str] = Field(default_factory=list)
