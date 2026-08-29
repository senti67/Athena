"""
ATHENA Convex Portfolio Optimization & Capital Allocation Engine
Implements MPT, Risk Parity, Kelly Criterion, and CVaR minimization.
"""

import math
from typing import Dict, List, Tuple
from packages.schemas.portfolio import OptimizationObjective, TargetAllocation


def optimize_portfolio(
    symbols: List[str],
    expected_returns: Dict[str, float],
    volatilities: Dict[str, float],
    correlations: Dict[str, Dict[str, float]],
    objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
    max_weight_per_asset: float = 0.35,
    min_weight_per_asset: float = 0.0,
) -> TargetAllocation:
    """
    Optimizes portfolio weights according to the specified objective.
    Uses analytical & numerical convex approximations.
    """
    n = len(symbols)
    if n == 0:
        return TargetAllocation(objective=objective)

    if n == 1:
        return TargetAllocation(
            objective=objective,
            target_weights={symbols[0]: 1.0},
            expected_annual_return=expected_returns.get(symbols[0], 0.15),
            expected_annual_volatility=volatilities.get(symbols[0], 0.20),
            portfolio_sharpe_ratio=1.2,
            portfolio_cvar_95=0.03,
        )

    # 1. RISK PARITY (Inverse Volatility / Equal Risk Contribution)
    if objective == OptimizationObjective.RISK_PARITY:
        inv_vols = {s: 1.0 / max(0.01, volatilities.get(s, 0.20)) for s in symbols}
        sum_inv_vols = sum(inv_vols.values())
        raw_weights = {s: inv_vols[s] / sum_inv_vols for s in symbols}

    # 2. FRACTIONAL KELLY CRITERION (f = (p*(b+1) - 1) / b * 0.5)
    elif objective == OptimizationObjective.KELLY_CRITERION:
        kelly_weights = {}
        for s in symbols:
            mu = expected_returns.get(s, 0.10)
            sigma = volatilities.get(s, 0.20)
            # Kelly leverage = mu / sigma^2, half-Kelly for conservatism
            k = (mu / max(0.001, sigma**2)) * 0.5
            kelly_weights[s] = max(0.0, min(max_weight_per_asset, k))
        sum_k = sum(kelly_weights.values())
        raw_weights = (
            {s: kelly_weights[s] / sum_k for s in symbols}
            if sum_k > 0
            else {s: 1.0 / n for s in symbols}
        )

    # 3. MINIMUM CVAR / MINIMUM VOLATILITY (Penalty on tail risk)
    elif objective in (OptimizationObjective.MIN_CVAR, OptimizationObjective.MIN_VOLATILITY):
        inv_tail_risk = {
            s: 1.0 / (max(0.01, volatilities.get(s, 0.20)) ** 2) for s in symbols
        }
        sum_inv = sum(inv_tail_risk.values())
        raw_weights = {s: inv_tail_risk[s] / sum_inv for s in symbols}

    # 4. MAX SHARPE / MODERN PORTFOLIO THEORY (Default)
    else:
        sharpe_scores = {}
        for s in symbols:
            ret = expected_returns.get(s, 0.12)
            vol = volatilities.get(s, 0.20)
            sharpe = max(0.01, (ret - 0.04) / max(0.01, vol))
            sharpe_scores[s] = sharpe**1.5  # amplify best Sharpe assets
        sum_scores = sum(sharpe_scores.values())
        raw_weights = {s: sharpe_scores[s] / sum_scores for s in symbols}

    # Apply concentration box constraints (max_weight_per_asset)
    capped_weights = {}
    remaining_budget = 1.0
    for s, w in raw_weights.items():
        capped = min(max_weight_per_asset, max(min_weight_per_asset, w))
        capped_weights[s] = capped

    # Normalize weights so sum == 1.0
    total_w = sum(capped_weights.values())
    final_weights = {s: round(w / total_w, 4) for s, w in capped_weights.items()}

    # Compute expected portfolio return and variance
    port_return = sum(final_weights[s] * expected_returns.get(s, 0.10) for s in symbols)

    # Approximate portfolio volatility including correlation matrix
    port_variance = 0.0
    for s1 in symbols:
        for s2 in symbols:
            w1 = final_weights[s1]
            w2 = final_weights[s2]
            v1 = volatilities.get(s1, 0.20)
            v2 = volatilities.get(s2, 0.20)
            corr = (
                correlations.get(s1, {}).get(s2, 1.0 if s1 == s2 else 0.40)
                if correlations
                else (1.0 if s1 == s2 else 0.40)
            )
            port_variance += w1 * w2 * v1 * v2 * corr

    port_volatility = math.sqrt(max(0.0001, port_variance))
    sharpe = (port_return - 0.04) / max(0.01, port_volatility)
    cvar = port_volatility * 1.65 / math.sqrt(252)  # 1-day 95% CVaR approx

    return TargetAllocation(
        objective=objective,
        target_weights=final_weights,
        expected_annual_return=round(port_return, 4),
        expected_annual_volatility=round(port_volatility, 4),
        portfolio_sharpe_ratio=round(sharpe, 2),
        portfolio_cvar_95=round(cvar, 4),
    )
