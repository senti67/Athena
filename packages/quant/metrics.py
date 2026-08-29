"""
ATHENA Risk and Performance Metrics Engine
Calculates institutional hedge fund risk metrics, VaR, CVaR, and return ratios.
"""

import math
from typing import List, Tuple


def calculate_returns(prices: List[float]) -> List[float]:
    """Computes simple periodic returns from a price series."""
    if len(prices) < 2:
        return []
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]


def calculate_log_returns(prices: List[float]) -> List[float]:
    """Computes log returns."""
    if len(prices) < 2:
        return []
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """Computes Compound Annual Growth Rate (CAGR)."""
    if start_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def calculate_sharpe_ratio(
    returns: List[float], risk_free_rate_annual: float = 0.04, periods_per_year: int = 252
) -> float:
    """Computes Annualized Sharpe Ratio."""
    if not returns or len(returns) < 5:
        return 0.0

    rf_periodic = risk_free_rate_annual / periods_per_year
    excess_returns = [r - rf_periodic for r in returns]
    mean_excess = sum(excess_returns) / len(excess_returns)

    variance = sum((r - mean_excess) ** 2 for r in excess_returns) / len(excess_returns)
    std = math.sqrt(variance)

    if std == 0:
        return 0.0
    return (mean_excess / std) * math.sqrt(periods_per_year)


def calculate_sortino_ratio(
    returns: List[float], risk_free_rate_annual: float = 0.04, periods_per_year: int = 252
) -> float:
    """Computes Annualized Sortino Ratio using downside semi-variance."""
    if not returns or len(returns) < 5:
        return 0.0

    rf_periodic = risk_free_rate_annual / periods_per_year
    excess_returns = [r - rf_periodic for r in returns]
    mean_excess = sum(excess_returns) / len(excess_returns)

    downside_diffs = [min(0.0, r) ** 2 for r in excess_returns]
    downside_std = math.sqrt(sum(downside_diffs) / len(returns))

    if downside_std == 0:
        return 0.0
    return (mean_excess / downside_std) * math.sqrt(periods_per_year)


def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int, int]:
    """
    Computes Maximum Drawdown percentage, peak index, and trough index.
    Returns: (max_drawdown_ratio, peak_idx, trough_idx)
    """
    if not equity_curve:
        return 0.0, 0, 0

    max_dd = 0.0
    peak = equity_curve[0]
    peak_idx = 0
    max_peak_idx = 0
    max_trough_idx = 0

    for i, val in enumerate(equity_curve):
        if val > peak:
            peak = val
            peak_idx = i
        dd = (peak - val) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
            max_peak_idx = peak_idx
            max_trough_idx = i

    return max_dd, max_peak_idx, max_trough_idx


def calculate_calmar_ratio(cagr: float, max_drawdown: float) -> float:
    """Computes Calmar Ratio = CAGR / Max Drawdown."""
    if max_drawdown <= 0.0001:
        return 0.0
    return cagr / max_drawdown


def calculate_var_historical(returns: List[float], confidence: float = 0.95) -> float:
    """Computes Historical Value at Risk (VaR) at given confidence (e.g. 95%)."""
    if not returns or len(returns) < 10:
        return 0.02
    sorted_returns = sorted(returns)
    index = int((1.0 - confidence) * len(sorted_returns))
    return abs(sorted_returns[max(0, index)])


def calculate_cvar_expected_shortfall(returns: List[float], confidence: float = 0.95) -> float:
    """
    Computes Conditional Value at Risk (CVaR / Expected Shortfall).
    Average loss beyond the VaR threshold.
    """
    if not returns or len(returns) < 10:
        return 0.035
    sorted_returns = sorted(returns)
    cutoff_index = max(1, int((1.0 - confidence) * len(sorted_returns)))
    tail_losses = sorted_returns[:cutoff_index]
    return abs(sum(tail_losses) / len(tail_losses))


def calculate_win_rate_and_profit_factor(
    trade_pnls: List[float],
) -> Tuple[float, float, float]:
    """
    Computes (win_rate, profit_factor, expectancy).
    """
    if not trade_pnls:
        return 0.0, 0.0, 0.0

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]

    win_rate = len(wins) / len(trade_pnls) if trade_pnls else 0.0
    gross_profits = sum(wins)
    gross_losses = abs(sum(losses))

    profit_factor = (
        gross_profits / gross_losses if gross_losses > 0 else (99.0 if gross_profits > 0 else 0.0)
    )
    expectancy = sum(trade_pnls) / len(trade_pnls)
    return win_rate, profit_factor, expectancy
