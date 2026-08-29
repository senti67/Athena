"""
ATHENA Offline Learning & Bayesian Calibration Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentWeightUpdate(BaseModel):
    agent_name: str
    previous_weight: float
    updated_weight: float
    delta: float
    historical_accuracy: float
    regime_specific_weights: Dict[str, float] = Field(default_factory=dict)
    rationale: str


class StrategyWeightUpdate(BaseModel):
    strategy_name: str
    previous_weight: float
    updated_weight: float
    delta: float
    sharpe_recent: float
    win_rate_recent: float
    rationale: str


class CalibrationMetrics(BaseModel):
    model_name: str
    brier_score: float = 0.12  # Lower is better (0 to 1)
    expected_calibration_error_ece: float = 0.04
    maximum_calibration_error_mce: float = 0.08
    platt_a_param: float = 1.0
    platt_b_param: float = 0.0
    reliability_curve_bins: List[Dict[str, float]] = Field(default_factory=list)


class LearningRunSummary(BaseModel):
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trades_analyzed: int
    overall_win_rate: float
    false_positives_count: int
    false_negatives_count: int
    agent_weight_updates: List[AgentWeightUpdate]
    strategy_weight_updates: List[StrategyWeightUpdate]
    calibration: CalibrationMetrics
    winning_conditions_insight: str
    losing_conditions_insight: str
    approval_status: str = "PENDING_OPERATOR_APPROVAL"
