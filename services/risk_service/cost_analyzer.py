"""
ATHENA Transaction Cost & Slippage Analyzer
Evaluates transaction friction, bid-ask spread cost, estimated market impact,
and exchange/regulatory fees relative to expected trade returns.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CostAnalysisResult(BaseModel):
    status: str = "PASS"  # "PASS", "WARN", "REJECT"
    symbol: str
    estimated_spread_cost_usd: float = 0.0
    estimated_slippage_usd: float = 0.0
    estimated_fees_usd: float = 0.0
    total_estimated_cost_usd: float = 0.0
    cost_to_return_ratio: float = 0.0
    reason: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TransactionCostAnalyzer:
    """
    Evaluates transaction feasibility before order placement.
    Rejects setups where transaction friction consumes an excessive fraction of expected alpha.
    """

    def __init__(self, max_cost_to_return_ratio: float = 0.35, warning_threshold: float = 0.20):
        self.max_cost_to_return_ratio = max_cost_to_return_ratio
        self.warning_threshold = warning_threshold

    def evaluate_cost(
        self,
        symbol: str,
        price: float,
        shares: int,
        expected_return_pct: float = 0.04,
        bid_ask_spread_bps: float = 4.0,
    ) -> CostAnalysisResult:
        if shares <= 0 or price <= 0:
            return CostAnalysisResult(
                status="PASS",
                symbol=symbol,
                reason="Zero or non-positive order size; no transaction costs."
            )

        notional_value = shares * price
        
        # 1. Half-spread cost (crossing the spread)
        spread_fraction = (bid_ask_spread_bps / 10000.0) / 2.0
        spread_cost = notional_value * spread_fraction

        # 2. Slippage estimate (modeled as 0.5 * spread)
        slippage_cost = notional_value * (spread_fraction * 0.5)

        # 3. SEC / FINRA / Broker regulatory fees (approx. $0.0001 per share + min fee)
        fees = max(0.01, shares * 0.0001)

        total_cost = spread_cost + slippage_cost + fees
        expected_gross_profit = notional_value * max(0.01, expected_return_pct)
        cost_ratio = total_cost / expected_gross_profit if expected_gross_profit > 0 else 1.0

        if cost_ratio > self.max_cost_to_return_ratio:
            status = "REJECT"
            reason = f"Transaction cost (${total_cost:.2f}) represents {cost_ratio:.1%} of expected gain (${expected_gross_profit:.2f}), exceeding {self.max_cost_to_return_ratio:.0%} limit."
        elif cost_ratio > self.warning_threshold:
            status = "WARN"
            reason = f"Elevated transaction cost friction ({cost_ratio:.1%} of expected gain)."
        else:
            status = "PASS"
            reason = f"Transaction friction nominal (${total_cost:.2f}, {cost_ratio:.1%} of expected gain)."

        return CostAnalysisResult(
            status=status,
            symbol=symbol,
            estimated_spread_cost_usd=round(spread_cost, 2),
            estimated_slippage_usd=round(slippage_cost, 2),
            estimated_fees_usd=round(fees, 2),
            total_estimated_cost_usd=round(total_cost, 2),
            cost_to_return_ratio=round(cost_ratio, 4),
            reason=reason,
        )


transaction_cost_analyzer = TransactionCostAnalyzer()
