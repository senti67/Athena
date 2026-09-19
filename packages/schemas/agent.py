"""
ATHENA V2 Core Research Agent Schemas
Defines the 6 Directional Research Agent types, structured outputs, and implementation statuses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .feature import FeatureSnapshot
from .regime import RegimeState


class AgentType(str, Enum):
    """The 6 Core Directional Research Agents of ATHENA V2."""
    TECHNICAL = "technical"
    QUANT = "quant"
    FUNDAMENTAL = "fundamental"
    SENTIMENT_NEWS = "sentiment_news"
    MACRO = "macro"
    MICROSTRUCTURE = "microstructure"

    # Legacy aliases for backward compatibility
    SENTIMENT = "sentiment_news"
    RESEARCH = "sentiment_news"
    PATTERN_DISCOVERY = "technical"
    SIMULATION = "quant"
    DATA_QUALITY = "technical"
    COMPLIANCE = "macro"
    COST_ANALYSIS = "microstructure"
    OPTIONS = "quant"
    CROSS_ASSET = "macro"


class AgentSignalType(str, Enum):
    """Permitted directional and operational actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    UNAVAILABLE = "UNAVAILABLE"


class ImplementationStatus(str, Enum):
    """Honest implementation readiness state."""
    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    PLACEHOLDER = "PLACEHOLDER"
    UNAVAILABLE = "UNAVAILABLE"


class EvidenceItem(BaseModel):
    category: str  # e.g., "technical", "momentum", "factor", "regime", "liquidity"
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
    order_book_data: Optional[Dict[str, Any]] = None
    extra_context: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent: AgentType = Field(alias="agent_name", default=AgentType.TECHNICAL)
    version: str = "2.0.0"
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signal: AgentSignalType = Field(alias="action", default=AgentSignalType.HOLD)
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0.0 if UNAVAILABLE)")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    data_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    features_used: List[str] = Field(default_factory=list)
    reasoning: str = Field(alias="reason", default="")
    implementation_status: ImplementationStatus = ImplementationStatus.IMPLEMENTED
    expected_return: float = Field(default=0.0)
    expected_risk: float = Field(default=0.0)
    holding_period_days: int = 5
    bullish_points: List[str] = Field(default_factory=list)
    bearish_points: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "v2-deterministic"
    tokens_used: int = 0
    latency_ms: int = 0

    class Config:
        populate_by_name = True

    @property
    def action(self) -> AgentSignalType:
        return self.signal

    @property
    def agent_name(self) -> AgentType:
        return self.agent

    @property
    def reason(self) -> str:
        return self.reasoning


class AgentRunSummary(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_outputs: Dict[str, AgentOutput]
    supporting_agents: List[str] = Field(default_factory=list)
    opposing_agents: List[str] = Field(default_factory=list)
    neutral_agents: List[str] = Field(default_factory=list)
    unavailable_agents: List[str] = Field(default_factory=list)
    aggregate_confidence: float = 0.0
    domain_diversity_score: float = 0.0
    qualitative_summary: str = ""
