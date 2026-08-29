"""
ATHENA Multi-Agent AI Framework Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .feature import FeatureSnapshot
from .regime import RegimeState


class AgentType(str, Enum):
    RESEARCH = "research"
    TECHNICAL = "technical"
    QUANT = "quant"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    MICROSTRUCTURE = "microstructure"
    OPTIONS = "options"
    CROSS_ASSET = "cross_asset"
    PATTERN_DISCOVERY = "pattern_discovery"
    SIMULATION = "simulation"
    DATA_QUALITY = "data_quality"
    COMPLIANCE = "compliance"
    COST_ANALYSIS = "cost_analysis"


class AgentSignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class EvidenceItem(BaseModel):
    category: str  # e.g., "technical_breakout", "earnings_growth", "macro_headwind"
    point: str
    weight: float = 1.0  # relative strength of this point
    is_bullish: bool = True


class AgentContext(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    feature_snapshot: FeatureSnapshot
    regime_state: Optional[RegimeState] = None
    historical_candles_count: int = 200
    portfolio_cash: float = 100000.0
    current_position: float = 0.0
    market_news: List[str] = Field(default_factory=list)
    macro_indicators: Dict[str, float] = Field(default_factory=dict)
    fundamental_metrics: Dict[str, float] = Field(default_factory=dict)
    extra_context: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent: AgentType
    version: str = "1.0.0"
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signal: AgentSignalType
    confidence: float = Field(ge=0.0, le=1.0, description="Raw model confidence")
    calibrated_probability: Optional[float] = Field(
        default=None, description="Platt-scaled empirical probability"
    )
    expected_return: float = Field(default=0.0, description="Estimated return percentage over horizon")
    expected_risk: float = Field(default=0.0, description="Estimated drawdown / risk percentage")
    holding_period_days: int = 5
    reasoning: str
    bullish_points: List[str] = Field(default_factory=list)
    bearish_points: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "gpt-4o"
    tokens_used: int = 0
    latency_ms: int = 0


class AgentRunSummary(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_outputs: Dict[str, AgentOutput]
    supporting_agents: List[str] = Field(default_factory=list)
    opposing_agents: List[str] = Field(default_factory=list)
    neutral_agents: List[str] = Field(default_factory=list)
    aggregate_confidence: float = 0.0
