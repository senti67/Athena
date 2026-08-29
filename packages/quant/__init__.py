"""Athena Quantitative Computing Package"""

from .indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_vwap,
    calculate_stochastic,
    calculate_support_resistance,
)
from .metrics import (
    calculate_returns,
    calculate_log_returns,
    calculate_cagr,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_var_historical,
    calculate_cvar_expected_shortfall,
    calculate_win_rate_and_profit_factor,
)
from .optimization import optimize_portfolio

__all__ = [
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_atr",
    "calculate_vwap",
    "calculate_stochastic",
    "calculate_support_resistance",
    "calculate_returns",
    "calculate_log_returns",
    "calculate_cagr",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_calmar_ratio",
    "calculate_var_historical",
    "calculate_cvar_expected_shortfall",
    "calculate_win_rate_and_profit_factor",
    "optimize_portfolio",
]
