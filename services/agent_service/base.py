"""
ATHENA Base AI Agent Interface
"""

import time
from abc import ABC, abstractmethod
from typing import Optional
from packages.logging.logger import get_logger
from packages.monitoring.metrics import AGENT_LATENCY
from packages.schemas.agent import AgentContext, AgentOutput, AgentType
from .llm_gateway import llm_gateway

logger = get_logger("athena.agent")


class BaseAgent(ABC):
    """Abstract base class for all ATHENA analytical and operational agents."""

    name: AgentType
    version: str = "1.0.0"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "gpt-4o"
        self.gateway = llm_gateway

    async def run(self, context: AgentContext) -> AgentOutput:
        """Wraps analyze() with latency instrumentation and error recovery."""
        start_time = time.perf_counter()
        try:
            output = await self.analyze(context)
            latency = time.perf_counter() - start_time
            AGENT_LATENCY.labels(agent_name=self.name.value).observe(latency)
            output.latency_ms = int(latency * 1000)
            return output
        except Exception as e:
            logger.error(f"Agent {self.name.value} error on {context.symbol}: {str(e)}", exc_info=True)
            # Fail-safe deterministic output
            return self._create_failsafe_output(context, str(e))

    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentOutput:
        """Agent-specific quantitative and LLM reasoning logic."""
        pass

    def _create_failsafe_output(self, context: AgentContext, error_msg: str) -> AgentOutput:
        from packages.schemas.agent import AgentSignalType
        return AgentOutput(
            agent=self.name,
            version=self.version,
            symbol=context.symbol,
            signal=AgentSignalType.HOLD,
            confidence=0.10,
            expected_return=0.0,
            expected_risk=0.01,
            reasoning=f"Failsafe mode activated due to error: {error_msg}",
            risk_flags=[f"AGENT_ERROR: {error_msg}"],
            model_version="failsafe",
        )
