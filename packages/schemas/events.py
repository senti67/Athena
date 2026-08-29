"""
ATHENA Event Bus Message Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field


class EventType(str, Enum):
    MARKET_DATA_RECEIVED = "MARKET_DATA_RECEIVED"
    DATA_QUALITY_FAILED = "DATA_QUALITY_FAILED"
    FEATURES_UPDATED = "FEATURES_UPDATED"
    REGIME_UPDATED = "REGIME_UPDATED"
    AGENT_ANALYSIS_COMPLETED = "AGENT_ANALYSIS_COMPLETED"
    STRATEGY_SIGNAL_GENERATED = "STRATEGY_SIGNAL_GENERATED"
    DEBATE_COMPLETED = "DEBATE_COMPLETED"
    DECISION_GENERATED = "DECISION_GENERATED"
    RISK_APPROVED = "RISK_APPROVED"
    RISK_REJECTED = "RISK_REJECTED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    TRADE_CLOSED = "TRADE_CLOSED"
    LEARNING_RUN_COMPLETED = "LEARNING_RUN_COMPLETED"
    WEIGHTS_UPDATED = "WEIGHTS_UPDATED"
    CIRCUIT_BREAKER_TRIGGERED = "CIRCUIT_BREAKER_TRIGGERED"


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    producer: str = "athena-core"
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0.0"
    payload: Dict[str, Any] = Field(default_factory=dict)
