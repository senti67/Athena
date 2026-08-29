"""
Unit Tests for Pure Math Indicators, Risk Metrics, and Convex Portfolio Optimizer
"""

import math
from packages.quant.indicators import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from packages.quant.metrics import (
    calculate_cagr,
    calculate_calmar_ratio,
    calculate_cvar_expected_shortfall,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_var_historical,
)
from packages.quant.optimization import optimize_portfolio
from packages.schemas.portfolio import OptimizationObjective


def test_technical_indicators():
    prices = [100.0 + (i * 0.5) for i in range(50)]

    sma_20 = calculate_sma(prices, 20)
    assert sma_20 > 0.0

    ema_9 = calculate_ema(prices, 9)
    assert ema_9 > 0.0

    rsi = calculate_rsi(prices, 14)
    assert 0.0 <= rsi <= 100.0

    macd, signal, hist = calculate_macd(prices)
    assert isinstance(macd, float)

    upper, mid, lower, bw = calculate_bollinger_bands(prices, 20, 2.0)
    assert upper >= mid >= lower
    assert bw >= 0.0


def test_risk_metrics():
    # 5% daily returns sequence
    returns = [0.01, -0.005, 0.02, -0.01, 0.015, 0.005, -0.008, 0.012, 0.004, -0.002]
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)
    var = calculate_var_historical(returns, 0.95)
    cvar = calculate_cvar_expected_shortfall(returns, 0.95)

    assert sharpe > 0.0
    assert sortino > 0.0
    assert var > 0.0
    assert cvar >= var, "CVaR (Expected Shortfall) must be >= VaR"

    equity_curve = [100.0, 105.0, 110.0, 99.0, 108.0, 115.0]
    max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity_curve)
    assert round(max_dd, 4) == round((110.0 - 99.0) / 110.0, 4)


def test_portfolio_optimization():
    symbols = ["AAPL", "NVDA", "MSFT"]
    expected_returns = {"AAPL": 0.15, "NVDA": 0.25, "MSFT": 0.18}
    volatilities = {"AAPL": 0.20, "NVDA": 0.35, "MSFT": 0.18}

    allocation = optimize_portfolio(
        symbols=symbols,
        expected_returns=expected_returns,
        volatilities=volatilities,
        correlations={},
        objective=OptimizationObjective.MAX_SHARPE,
    )

    assert len(allocation.target_weights) == 3
    total_w = sum(allocation.target_weights.values())
    assert abs(total_w - 1.0) < 0.01, f"Total weight must sum to 1.0, got {total_w}"
    assert allocation.portfolio_sharpe_ratio > 0.0
