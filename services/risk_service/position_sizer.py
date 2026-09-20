"""
ATHENA Volatility & ATR-Aware Position Sizing Engine
Calculates optimal share quantities constrained by ATR risk budget, portfolio NAV,
and institutional position limits ($25,000 max size and 20% single-asset NAV cap).
"""

import math
from typing import Dict, Any, Optional
from packages.common.config import settings
from packages.logging.logger import get_logger

logger = get_logger("athena.position_sizer")


class PositionSizer:
    """
    Computes institutional share sizing using ATR risk budgeting,
    portfolio NAV caps, and cash constraints.
    """

    def __init__(
        self,
        risk_per_trade_pct: float = 0.015,  # 1.5% NAV risk per trade
        max_position_size_usd: float = settings.MAX_POSITION_SIZE,  # $25,000
        max_single_asset_exposure: float = settings.MAX_SINGLE_ASSET_EXPOSURE,  # 20% NAV
    ):
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_position_size_usd = max_position_size_usd
        self.max_single_asset_exposure = max_single_asset_exposure

    def calculate_position_size(
        self,
        symbol: str,
        current_price: float,
        atr_14: float,
        portfolio_nav: float,
        available_cash: float,
        confidence: float = 0.80,
    ) -> Dict[str, Any]:
        """
        Calculates suggested shares based on ATR volatility and risk limits.
        """
        if current_price <= 0:
            return {"shares": 0, "notional_usd": 0.0, "reason": "Invalid price"}

        # Effective ATR (fallback to 2% of price if ATR is 0)
        effective_atr = atr_14 if atr_14 > 0 else (current_price * 0.02)
        stop_distance = max(current_price * 0.01, effective_atr * 1.5)

        # 1. Dollar risk budget based on NAV and confidence scaling
        risk_budget_usd = portfolio_nav * self.risk_per_trade_pct * min(1.2, max(0.8, confidence))

        # 2. Shares based on stop distance
        shares_by_risk = math.floor(risk_budget_usd / stop_distance)

        # 3. Shares based on maximum dollar position size ($25,000)
        shares_by_cap = math.floor(self.max_position_size_usd / current_price)

        # 4. Shares based on single asset NAV cap (e.g. 20% of NAV)
        shares_by_nav = math.floor((portfolio_nav * self.max_single_asset_exposure) / current_price)

        # 5. Shares based on cash availability (leaving reserve only if MIN_BUYING_POWER_RESERVE > 0)
        usable_cash = max(
            0.0,
            available_cash - (
                settings.MIN_BUYING_POWER_RESERVE
                if settings.MIN_BUYING_POWER_RESERVE > 0 and portfolio_nav > settings.MIN_BUYING_POWER_RESERVE
                else 0.0
            )
        )
        shares_by_cash = math.floor(usable_cash / current_price)

        # Final suggested shares
        suggested_shares = max(0, min(shares_by_risk, shares_by_cap, shares_by_nav, shares_by_cash))
        notional_usd = suggested_shares * current_price

        return {
            "shares": int(suggested_shares),
            "notional_usd": round(notional_usd, 2),
            "risk_budget_usd": round(risk_budget_usd, 2),
            "stop_distance": round(stop_distance, 2),
            "shares_by_risk": int(shares_by_risk),
            "shares_by_cap": int(shares_by_cap),
            "shares_by_nav": int(shares_by_nav),
            "shares_by_cash": int(shares_by_cash),
        }


position_sizer = PositionSizer()
