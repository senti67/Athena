"""
Unit Tests for ATHENA 16 Quantitative Strategies
"""

import pytest
from packages.schemas.agent import AgentContext
from packages.schemas.strategy import StrategySignal
from services.data_service.providers import MockMarketDataProvider
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector
from services.strategy_service.registry import strategy_registry


@pytest.mark.asyncio
async def test_all_16_strategies_execute_and_produce_signals():
    provider = MockMarketDataProvider()
    candles = await provider.get_ohlcv("NVDA", limit=100)
    features = feature_pipeline.compute_features("NVDA", candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol="NVDA",
        feature_snapshot=features,
        regime_state=regime,
    )

    outputs = strategy_registry.run_all_strategies(context)

    assert len(outputs) == 16, "All 16 strategies must execute and return valid outputs"
    for strat_name, out in outputs.items():
        assert out.symbol == "NVDA"
        assert out.confidence >= 0.0 and out.confidence <= 1.0
        assert out.signal in (StrategySignal.BUY, StrategySignal.SELL, StrategySignal.HOLD)
        assert out.stop_loss_pct > 0.0
        assert out.take_profit_pct > 0.0
