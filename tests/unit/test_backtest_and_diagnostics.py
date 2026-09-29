"""
Unit Tests for Backtesting Engine and Performance Diagnostics
"""

import pytest
from packages.schemas.backtest import BacktestConfig
from services.backtest_service.engine import backtest_engine
from services.backtest_service.performance_analyzer import performance_analyzer


@pytest.mark.asyncio
async def test_backtest_runs_and_produces_diagnostics():
    config = BacktestConfig(
        backtest_id="bt-unit-test",
        symbols=["AAPL", "MSFT"],
        initial_cash=50000.0,
        slippage_bps=5.0,
        commission_per_share=0.005,
        strategies_enabled=["trend_following", "momentum", "mean_reversion", "breakout"],
    )

    result = await backtest_engine.run_backtest(config)

    assert result.status == "COMPLETED"
    assert result.metrics.total_return_pct is not None
    assert result.metrics.sharpe_ratio is not None
    assert result.metrics.max_drawdown_pct is not None
    assert len(result.equity_curve) > 0

    report = performance_analyzer.generate_diagnostic_report(result)
    assert "EXECUTIVE PERFORMANCE SUMMARY" in report
    assert "REGIME-CONDITIONED PERFORMANCE BREAKDOWN" in report
    assert "MONTE CARLO PROJECTIONS" in report
