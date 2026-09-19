"""
ATHENA V2 Base Research Agent Interface
Provides standardized asynchronous execution, strict per-agent timeout handling,
latency metrics, and deterministic UNAVAILABLE failsafe output.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Optional
from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.monitoring.metrics import AGENT_LATENCY
from packages.schemas.agent import (
    AgentContext,
    AgentOutput,
    AgentSignalType,
    AgentType,
    ImplementationStatus,
)
from .llm_gateway import llm_gateway

logger = get_logger("athena.agent")


class BaseAgent(ABC):
    """Abstract base class for ATHENA V2 Directional Research Agents."""

    name: AgentType
    version: str = "2.0.0"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.LLM_PRIMARY_MODEL
        self.gateway = llm_gateway
        self.timeout_seconds = settings.AGENT_TIMEOUT_SECONDS

    async def run(self, context: AgentContext) -> AgentOutput:
        """
        Executes analyze() wrapped with strict async timeout and latency instrumentation.
        If an agent times out or crashes, returns UNAVAILABLE (confidence=0.0).
        """
        start_time = time.perf_counter()
        try:
            output = await asyncio.wait_for(
                self.analyze(context),
                timeout=self.timeout_seconds,
            )
            latency = time.perf_counter() - start_time
            AGENT_LATENCY.labels(agent_name=self.name.value).observe(latency)
            output.latency_ms = int(latency * 1000)
            return output
        except asyncio.TimeoutError:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(
                f"Agent {self.name.value} timed out after {self.timeout_seconds}s on {context.symbol}"
            )
            return self._create_unavailable_output(
                context, f"Execution timed out after {self.timeout_seconds}s", latency_ms
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                f"Agent {self.name.value} error on {context.symbol}: {str(e)}",
                exc_info=True,
            )
            return self._create_unavailable_output(context, str(e), latency_ms)

    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentOutput:
        """Agent-specific directional research logic."""
        pass

    def _create_unavailable_output(
        self, context: AgentContext, reason_msg: str, latency_ms: int = 0
    ) -> AgentOutput:
        """Returns structured UNAVAILABLE output with confidence=0.0."""
        return AgentOutput(
            agent=self.name,
            version=self.version,
            symbol=context.symbol,
            signal=AgentSignalType.UNAVAILABLE,
            confidence=0.0,
            expected_return=0.0,
            expected_risk=0.0,
            reasoning=f"Agent research unavailable: {reason_msg}",
            risk_flags=[f"AGENT_UNAVAILABLE: {reason_msg}"],
            implementation_status=ImplementationStatus.UNAVAILABLE,
            model_version="failsafe-v2",
            latency_ms=latency_ms,
        )
