"""
ATHENA Dialectical Debate Engine Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ConflictItem(BaseModel):
    agents_involved: List[str]
    topic: str  # e.g., "valuation vs momentum"
    agent_a_position: str
    agent_b_position: str
    severity: float = Field(ge=0.0, le=1.0, description="Contradiction severity")
    resolution: str


class DebateReport(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agreement_score: float = Field(
        ge=0.0, le=1.0, description="Consensus metric across all agents"
    )
    conflicts: List[ConflictItem] = Field(default_factory=list)
    strongest_bullish_evidence: List[str] = Field(default_factory=list)
    strongest_bearish_evidence: List[str] = Field(default_factory=list)
    weakest_evidence: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    bull_count: int = 0
    bear_count: int = 0
    neutral_count: int = 0
    debate_synthesis: str
    recommended_action: str  # "BUY", "SELL", "HOLD"
    consensus_confidence: float = Field(ge=0.0, le=1.0)
