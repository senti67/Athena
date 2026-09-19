"""
Unit Tests for ATHENA V2 6 Directional Research Agents & Truthfulness Invariants
"""

import pytest
import asyncio
from packages.schemas.agent import AgentContext, AgentSignalType, AgentType, ImplementationStatus
from services.agent_service.orchestrator import agent_orchestrator
from services.agent_service.agents import FundamentalAgent, SentimentNewsAgent, MicrostructureAgent, TechnicalAgent
from services.data_service.providers import MockMarketDataProvider
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector


@pytest.mark.asyncio
async def test_all_6_research_agents_produce_structured_output():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("AAPL", limit=100)
    features = feature_pipeline.compute_features("AAPL", candles)
    regime = regime_detector.detect_regime(features)

    # Provide real metrics to test active evaluation
    context = AgentContext(
        symbol="AAPL",
        feature_snapshot=features,
        regime_state=regime,
        fundamental_metrics={"pe_ratio": 24.5, "roe": 0.28, "debt_to_equity": 0.65, "fcf_yield": 0.045},
        market_news=["Apple beats earnings expectations with record iPhone revenue"],
    )

    summary = await agent_orchestrator.run_all_agents(context)

    # Exactly 6 research agents
    assert len(summary.agent_outputs) == 6, "Athena V2 must have exactly 6 Core Research Agents"
    assert summary.aggregate_confidence >= 0.0 and summary.aggregate_confidence <= 1.0

    expected_agents = {
        AgentType.TECHNICAL.value,
        AgentType.QUANT.value,
        AgentType.FUNDAMENTAL.value,
        AgentType.SENTIMENT_NEWS.value,
        AgentType.MACRO.value,
        AgentType.MICROSTRUCTURE.value,
    }
    assert set(summary.agent_outputs.keys()) == expected_agents

    for agent_name, out in summary.agent_outputs.items():
        assert out.symbol == "AAPL"
        assert out.confidence >= 0.0 and out.confidence <= 1.0
        assert out.signal in (AgentSignalType.BUY, AgentSignalType.SELL, AgentSignalType.HOLD, AgentSignalType.UNAVAILABLE)
        assert isinstance(out.reasoning, str) and len(out.reasoning) > 0


@pytest.mark.asyncio
async def test_truthfulness_missing_data_returns_unavailable():
    """Verifies that missing fundamental/sentiment/microstructure data returns UNAVAILABLE with 0.0 confidence."""
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("AAPL", limit=100)
    features = feature_pipeline.compute_features("AAPL", candles)
    
    # Zero out liquidity so MicrostructureAgent has no data
    features.liquidity.bid_ask_spread_bps = 0.0
    features.liquidity.depth_imbalance = 0.0
    # Zero out NLP so SentimentNewsAgent has no data
    features.nlp.sentiment_score = 0.0
    features.nlp.bullish_percentage = 0.5

    context = AgentContext(
        symbol="AAPL",
        feature_snapshot=features,
        fundamental_metrics={},  # Empty fundamentals
        market_news=[],          # Empty news
        order_book_data=None,    # Empty order book
    )

    fund_agent = FundamentalAgent()
    fund_out = await fund_agent.run(context)
    assert fund_out.signal == AgentSignalType.UNAVAILABLE
    assert fund_out.confidence == 0.0
    assert fund_out.implementation_status == ImplementationStatus.UNAVAILABLE
    assert "NO_FUNDAMENTAL_DATA" in fund_out.risk_flags

    sent_agent = SentimentNewsAgent()
    sent_out = await sent_agent.run(context)
    assert sent_out.signal == AgentSignalType.UNAVAILABLE
    assert sent_out.confidence == 0.0
    assert sent_out.implementation_status == ImplementationStatus.UNAVAILABLE

    micro_agent = MicrostructureAgent()
    micro_out = await micro_agent.run(context)
    assert micro_out.signal == AgentSignalType.UNAVAILABLE
    assert micro_out.confidence == 0.0
    assert micro_out.implementation_status == ImplementationStatus.UNAVAILABLE


@pytest.mark.asyncio
async def test_agent_timeout_handling():
    """Verifies that an agent timeout returns UNAVAILABLE without crashing."""
    class SlowAgent(TechnicalAgent):
        async def analyze(self, context: AgentContext):
            await asyncio.sleep(6.0)  # Exceeds AGENT_TIMEOUT_SECONDS = 5.0
            return await super().analyze(context)

    slow_agent = SlowAgent()
    slow_agent.timeout_seconds = 0.1  # Fast timeout for test

    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("AAPL", limit=100)
    features = feature_pipeline.compute_features("AAPL", candles)
    context = AgentContext(symbol="AAPL", feature_snapshot=features)

    out = await slow_agent.run(context)
    assert out.signal == AgentSignalType.UNAVAILABLE
    assert out.confidence == 0.0
    assert "timed out" in out.reasoning.lower()
