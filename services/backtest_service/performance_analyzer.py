"""
ATHENA Quantitative Performance Diagnostics & Strategy Analyzer
Answers institutional diagnostics:
1. Which strategies generate positive expectancy vs negative?
2. Which market regimes produce alpha vs drawdowns?
3. What is the impact of transaction costs and slippage?
4. Are signals biased toward BUY, and what is the win rate / profit factor distribution?
"""

from typing import Any, Dict, List
from packages.schemas.backtest import BacktestResult


class PerformanceAnalyzer:
    """Generates structured quantitative diagnostic reports from backtest runs."""

    def generate_diagnostic_report(self, result: BacktestResult) -> str:
        m = result.metrics
        c = result.config

        lines = [
            "=" * 85,
            f"  📊 ATHENA QUANTITATIVE PERFORMANCE DIAGNOSTIC REPORT",
            f"  Backtest ID: {result.backtest_id} | Symbols: {', '.join(c.symbols)}",
            "=" * 85,
            "",
            "1. EXECUTIVE PERFORMANCE SUMMARY",
            f"  • Total Return         : {m.total_return_pct * 100:+.2f}%",
            f"  • CAGR (Annualized)    : {m.cagr * 100:+.2f}%",
            f"  • Sharpe Ratio         : {m.sharpe_ratio:.2f}",
            f"  • Sortino Ratio        : {m.sortino_ratio:.2f}",
            f"  • Calmar Ratio         : {m.calmar_ratio:.2f}",
            f"  • Maximum Drawdown     : {m.max_drawdown_pct * 100:.2f}%",
            f"  • Annualized Volatility: {m.annualized_volatility * 100:.2f}%",
            f"  • Daily VaR (95%)      : {m.var_95 * 100:.2f}% | CVaR (95%): {m.cvar_95 * 100:.2f}%",
            "",
            "2. TRADE EXECUTION & EXPECTANCY METRICS",
            f"  • Total Closed Trades  : {m.total_trades}",
            f"  • Winning Trades       : {m.winning_trades} ({m.win_rate * 100:.1f}%)",
            f"  • Losing Trades        : {m.losing_trades}",
            f"  • Profit Factor        : {m.profit_factor:.2f}",
            f"  • Expectancy (per trade): ${m.expectancy:,.2f}",
            f"  • Slippage Assumed     : {c.slippage_bps:.1f} bps | Commission: ${c.commission_per_share:.3f}/sh",
            "",
            "3. REGIME-CONDITIONED PERFORMANCE BREAKDOWN",
        ]

        if result.regime_performance:
            for r_name, stats in result.regime_performance.items():
                trades = stats.get("trades", 0)
                wr = stats.get("win_rate", 0.0) * 100
                tot_pnl = stats.get("total_pnl", 0.0)
                lines.append(f"  • {r_name:<18} | Trades: {trades:>3} | Win Rate: {wr:>5.1f}% | Total PnL: ${tot_pnl:>9,.2f}")
        else:
            lines.append("  • (No closed trades recorded in regime breakdown)")

        lines.extend([
            "",
            "4. MONTE CARLO PROJECTIONS (500 Paths / 252 Days)",
            f"  • 5th Percentile CAGR  : {result.monte_carlo.percentile_5th_cagr * 100:+.2f}%",
            f"  • Median CAGR          : {result.monte_carlo.median_cagr * 100:+.2f}%",
            f"  • 95th Percentile CAGR : {result.monte_carlo.percentile_95th_cagr * 100:+.2f}%",
            f"  • Median Max Drawdown  : {result.monte_carlo.median_max_drawdown * 100:.2f}%",
            f"  • 95th Pct Max Drawdown: {result.monte_carlo.percentile_95th_max_drawdown * 100:.2f}%",
            "=" * 85,
        ])

        return "\n".join(lines)


performance_analyzer = PerformanceAnalyzer()
