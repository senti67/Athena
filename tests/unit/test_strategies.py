"""
Unit Tests for ATHENA V2 5 Active Quantitative Strategies & Dynamic StrategyEngine
"""

import pytest
from packages.schemas.agent import AgentContext, ImplementationStatus
from packages.schemas.regime import MarketRegimeType, RegimeState
from packages.schemas.strategy import StrategySignal, StrategyType
from services.data_service.providers import MockMarketDataProvider
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector
from services.strategy_service.engine import strategy_engine
from services.strategy_service.registry import strategy_registry


@pytest.mark.asyncio
async def test_5_active_strategies_execute_and_produce_signals():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("NVDA", limit=100)
    features = feature_pipeline.compute_features("NVDA", candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol="NVDA",
        feature_snapshot=features,
        regime_state=regime,
    )

    outputs = strategy_registry.run_all_strategies(context, active_only=True)

    assert len(outputs) == 5, "Athena V2 must have exactly 5 Active Production Strategies"
    expected_active = {
        StrategyType.TREND_FOLLOWING.value,
        StrategyType.MOMENTUM.value,
        StrategyType.MEAN_REVERSION.value,
        StrategyType.BREAKOUT.value,
        StrategyType.PULLBACK.value,
    }
    assert set(outputs.keys()) == expected_active

    for strat_name, out in outputs.items():
        assert out.symbol == "NVDA"
        assert out.confidence >= 0.0 and out.confidence <= 1.0
        assert out.signal in (StrategySignal.BUY, StrategySignal.SELL, StrategySignal.HOLD)
        assert out.stop_loss_pct > 0.0
        assert out.take_profit_pct > 0.0
        assert out.is_active is True
        assert out.implementation_status == ImplementationStatus.IMPLEMENTED


@pytest.mark.asyncio
async def test_disabled_strategies_are_inactive():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("NVDA", limit=100)
    features = feature_pipeline.compute_features("NVDA", candles)

    context = AgentContext(symbol="NVDA", feature_snapshot=features)
    all_outputs = strategy_registry.run_all_strategies(context, active_only=False)

    assert len(all_outputs) == 16
    # Check that disabled strategies are flagged correctly
    for name in ["swing", "pairs", "machine_learning", "reinforcement_learning", "value"]:
        assert name in all_outputs
        out = all_outputs[name]
        assert out.is_active is False
        assert out.signal == StrategySignal.UNAVAILABLE
        assert out.confidence == 0.0


@pytest.mark.asyncio
async def test_strategy_engine_regime_weighting():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("NVDA", limit=100)
    features = feature_pipeline.compute_features("NVDA", candles)

    # Mock a RegimeState with high trend following suitability
    regime = RegimeState(
        regime=MarketRegimeType.BULL,
        confidence=0.90,
        strategy_suitability_weights={"trend_following": 1.30, "mean_reversion": 0.50},
    )

    context = AgentContext(
        symbol="NVDA",
        feature_snapshot=features,
        regime_state=regime,
    )

    best_setup, outputs = strategy_engine.evaluate_strategies(context)
    assert len(outputs) == 5
    assert "trend_following" in outputs
    # Regime weight applied
    assert "Regime suitability weight: 1.30x" in outputs["trend_following"].rationale
