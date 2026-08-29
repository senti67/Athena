"""
ATHENA Base Quantitative Strategy Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from packages.schemas.agent import AgentContext
from packages.schemas.strategy import StrategyOutput, StrategySignal, StrategyType


class BaseStrategy(ABC):
    """Abstract interface for all independent quantitative trading strategies."""

    name: StrategyType
    description: str = ""
    default_holding_period: str = "5D"

    @abstractmethod
    def generate_signal(self, context: AgentContext) -> StrategyOutput:
        """Generates a structured trading signal given feature snapshot and market context."""
        pass
