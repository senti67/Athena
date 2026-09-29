"""
Unit Tests for Pure Quantitative Indicators and Math Functions
"""

import math
import pytest
from packages.quant.indicators import (
    calculate_adx,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_ema_slope,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from packages.quant.metrics import (
    calculate_autocorrelation,
    calculate_cagr,
    calculate_calmar_ratio,
    calculate_cvar_expected_shortfall,
    calculate_expected_edge,
    calculate_kurtosis,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_skewness,
    calculate_sortino_ratio,
    calculate_var_historical,
    calculate_win_rate_and_profit_factor,
)
from packages.schemas.market import Candle


def test_adx_calculation():
    # Construct rising candles
    candles = []
    base_price = 100.0
    for i in range(40):
        c = Candle(
            symbol="TEST",
            timestamp=f"2026-01-{i+1:02d}T00:00:00Z" if i < 30 else f"2026-02-{i-29:02d}T00:00:00Z",
            open=base_price + i,
            high=base_price + i + 1.5,
            low=base_price + i - 0.5,
            close=base_price + i + 1.0,
            volume=10000.0,
        )
        candles.append(c)

    adx, plus_di, minus_di = calculate_adx(candles, period=14)
    assert adx > 0.0
    assert plus_di >= 0.0
    assert minus_di >= 0.0
    # Uptrend should have plus_di > minus_di
    assert plus_di > minus_di


def test_ema_slope():
    rising_prices = [100.0 + (i * 2.0) for i in range(40)]
    slope_up = calculate_ema_slope(rising_prices, window=21, lookback=5)
    assert slope_up > 0.0

    falling_prices = [200.0 - (i * 2.0) for i in range(40)]
    slope_down = calculate_ema_slope(falling_prices, window=21, lookback=5)
    assert slope_down < 0.0


def test_skewness_and_kurtosis():
    symmetric_returns = [-0.02, -0.01, 0.0, 0.01, 0.02] * 10
    skew = calculate_skewness(symmetric_returns)
    assert abs(skew) < 0.1

    kurt = calculate_kurtosis(symmetric_returns)
    assert kurt > 0.0


def test_autocorrelation():
    trend_returns = [0.01] * 20
    autocorr = calculate_autocorrelation(trend_returns, lag=1)
    assert isinstance(autocorr, float)


def test_expected_edge_formula():
    # 60% win rate, 6% target, 2.5% stop
    # EV = 0.60 * 0.06 - 0.40 * 0.025 = 0.036 - 0.010 = 0.026 (+2.6%)
    ev = calculate_expected_edge(win_rate=0.60, take_profit_pct=0.06, stop_loss_pct=0.025)
    assert round(ev, 4) == 0.0260

    # 40% win rate, 2% target, 4% stop -> negative expectancy
    ev_neg = calculate_expected_edge(win_rate=0.40, take_profit_pct=0.02, stop_loss_pct=0.04)
    assert ev_neg < 0.0
