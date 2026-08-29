"""
Unit Tests for ATHENA 14 AI Analytical Agents
"""

import pytest
from packages.schemas.agent import AgentContext, AgentSignalType, AgentType
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.providers import MockMarketDataProvider
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector


@pytest.mark.asyncio
async def test_all_14_agents_produce_structured_output():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("AAPL", limit=100)
    features = feature_pipeline.compute_features("AAPL", candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol="AAPL",
        feature_snapshot=features,
        regime_state=regime,
    )

    summary = await agent_orchestrator.run_all_agents(context)

    assert len(summary.agent_outputs) == 14, "All 14 agents must execute and report"
    assert summary.aggregate_confidence >= 0.0 and summary.aggregate_confidence <= 1.0

    for agent_name, out in summary.agent_outputs.items():
        assert out.symbol == "AAPL"
        assert out.confidence >= 0.0 and out.confidence <= 1.0
        assert out.signal in (AgentSignalType.BUY, AgentSignalType.SELL, AgentSignalType.HOLD)
        assert isinstance(out.reasoning, str) and len(out.reasoning) > 0
