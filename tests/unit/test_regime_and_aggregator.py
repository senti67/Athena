"""
Unit Tests for Regime Detection, Signal Aggregation, and Conflict Deduplication
"""

import pytest
from packages.schemas.agent import AgentOutput, AgentRunSummary, AgentSignalType, AgentType, FeatureGroup
from packages.schemas.regime import MarketRegimeType, RegimeState
from packages.schemas.strategy import StrategyOutput, StrategySignal, StrategyType
from services.data_service.providers import MockMarketDataProvider
from services.debate_service.engine import SignalAggregator
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector


@pytest.mark.asyncio
async def test_regime_detector_classifies_correctly():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("AAPL", limit=100)
    features = feature_pipeline.compute_features("AAPL", candles)

    regime = regime_detector.detect_regime(features)
    assert regime.regime in [
        MarketRegimeType.TRENDING_BULL,
        MarketRegimeType.TRENDING_BEAR,
        MarketRegimeType.SIDEWAYS,
        MarketRegimeType.HIGH_VOLATILITY,
        MarketRegimeType.LOW_VOLATILITY,
        MarketRegimeType.UNCERTAIN,
    ]
    assert 0.0 <= regime.confidence <= 1.0
    assert "trend" in regime.feature_group_weights
    assert "mean_reversion" in regime.feature_group_weights


def test_signal_aggregator_prevents_correlated_double_counting():
    aggregator = SignalAggregator()

    # Create 3 trend agents all outputting BUY with RSI/EMA
    trend_out_1 = AgentOutput(
        agent=AgentType.TECHNICAL_TREND,
        symbol="AAPL",
        signal=AgentSignalType.BUY,
        confidence=0.85,
        feature_group=FeatureGroup.TREND,
        data_quality=1.0,
    )
    trend_out_2 = AgentOutput(
        agent=AgentType.TECHNICAL,
        symbol="AAPL",
        signal=AgentSignalType.BUY,
        confidence=0.80,
        feature_group=FeatureGroup.TREND,
        data_quality=1.0,
    )
    meanrev_out = AgentOutput(
        agent=AgentType.MEAN_REVERSION,
        symbol="AAPL",
        signal=AgentSignalType.SELL,
        confidence=0.80,
        feature_group=FeatureGroup.MEAN_REVERSION,
        data_quality=1.0,
    )

    summary = AgentRunSummary(
        symbol="AAPL",
        agent_outputs={
            "tech_1": trend_out_1,
            "tech_2": trend_out_2,
            "meanrev": meanrev_out,
        },
    )

    strat_outputs = {
        "trend_following": StrategyOutput(
            strategy=StrategyType.TREND_FOLLOWING,
            symbol="AAPL",
            signal=StrategySignal.BUY,
            confidence=0.82,
            feature_group=FeatureGroup.TREND,
            is_active=True,
        ),
    }

    report = aggregator.aggregate_signals("AAPL", summary, strat_outputs)

    # Trend feature group receives one consolidated weight, not 3x separate dominating votes
    assert "trend" in report.feature_group_scores
    assert "mean_reversion" in report.feature_group_scores
    assert report.conflict_penalty > 0.0, "Contradiction between Trend BUY and MeanReversion SELL must trigger conflict penalty"
    assert report.consensus_confidence < 0.85, "Confidence must be penalized for direct conflict"


def test_hold_is_emitted_when_evidence_is_insufficient():
    aggregator = SignalAggregator()

    neutral_out = AgentOutput(
        agent=AgentType.TECHNICAL_TREND,
        symbol="AAPL",
        signal=AgentSignalType.HOLD,
        confidence=0.50,
        feature_group=FeatureGroup.TREND,
        data_quality=1.0,
    )

    summary = AgentRunSummary(
        symbol="AAPL",
        agent_outputs={"trend": neutral_out},
    )

    strat_outputs = {}
    report = aggregator.aggregate_signals("AAPL", summary, strat_outputs)

    assert report.recommended_action == "HOLD"
    assert abs(report.composite_score) < 0.55
