"""
ATHENA Portfolio Manager & Dynamic Position Sizing Service
"""

from typing import Dict, List, Optional
from packages.logging.logger import get_logger
from packages.quant.optimization import optimize_portfolio
from packages.schemas.portfolio import (
    OptimizationObjective,
    PortfolioState,
    Position,
    TargetAllocation,
)

logger = get_logger("athena.portfolio_service")


class PortfolioManager:
    """Manages active holdings, state calculations, and portfolio optimization."""

    def __init__(self, initial_cash: float = 100000.0):
        self.state = PortfolioState(
            account_id="ATHENA_ALPHA_PORTFOLIO",
            nav=initial_cash,
            cash=initial_cash,
            positions={},
        )

    def get_portfolio_state(self) -> PortfolioState:
        """Computes current NAV, exposures, and unrealized PnL."""
        total_market_val = sum(p.market_value for p in self.state.positions.values())
        nav = self.state.cash + total_market_val
        self.state.nav = round(nav, 2)
        self.state.gross_exposure = round(total_market_val / nav if nav > 0 else 0.0, 4)
        self.state.net_exposure = self.state.gross_exposure
        self.state.leverage = self.state.gross_exposure
        self.state.total_positions_count = len(self.state.positions)

        # Update position weights
        for p in self.state.positions.values():
            p.portfolio_weight = round(p.market_value / nav if nav > 0 else 0.0, 4)

        return self.state

    def update_position_from_fill(
        self,
        symbol: str,
        side: str,
        shares: float,
        price: float,
        fee: float = 0.0,
    ):
        """Updates portfolio state immediately following an executed order fill."""
        self.state.cash -= fee
        if side == "BUY":
            cost = shares * price
            self.state.cash -= cost
            if symbol in self.state.positions:
                existing = self.state.positions[symbol]
                new_shares = existing.shares + shares
                new_avg = ((existing.shares * existing.average_entry_price) + cost) / new_shares
                existing.shares = new_shares
                existing.average_entry_price = round(new_avg, 2)
                existing.current_price = price
                existing.market_value = round(new_shares * price, 2)
                existing.unrealized_pnl = round(existing.market_value - (new_shares * new_avg), 2)
            else:
                self.state.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    average_entry_price=price,
                    current_price=price,
                    market_value=round(shares * price, 2),
                    cost_basis=round(cost, 2),
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0,
                    portfolio_weight=0.0,
                )
        elif side == "SELL":
            proceeds = shares * price
            self.state.cash += proceeds
            if symbol in self.state.positions:
                pos = self.state.positions[symbol]
                realized = (price - pos.average_entry_price) * shares
                self.state.daily_realized_pnl += realized
                self.state.total_pnl += realized
                pos.shares -= shares
                if pos.shares <= 0.001:
                    del self.state.positions[symbol]
                else:
                    pos.market_value = round(pos.shares * price, 2)
                    pos.unrealized_pnl = round((price - pos.average_entry_price) * pos.shares, 2)

        self.get_portfolio_state()
        logger.info(f"Portfolio updated: NAV=${self.state.nav:,.2f}, Cash=${self.state.cash:,.2f}, Positions={len(self.state.positions)}")

    def optimize_allocation(
        self,
        symbols: List[str],
        expected_returns: Optional[Dict[str, float]] = None,
        volatilities: Optional[Dict[str, float]] = None,
        objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
    ) -> TargetAllocation:
        """Executes convex portfolio optimization."""
        returns_map = expected_returns or {s: 0.12 + (i * 0.02) for i, s in enumerate(symbols)}
        vols_map = volatilities or {s: 0.18 + (i * 0.015) for i, s in enumerate(symbols)}

        return optimize_portfolio(
            symbols=symbols,
            expected_returns=returns_map,
            volatilities=vols_map,
            correlations={},
            objective=objective,
        )


portfolio_manager = PortfolioManager()
