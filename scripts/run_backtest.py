"""
ATHENA Event-Driven Backtest Runner Script
"""

import asyncio
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.schemas.backtest import BacktestConfig
from services.backtest_service.engine import backtest_engine


async def main():
    print("=" * 80)
    print("  ATHENA EVENT-DRIVEN QUANTITATIVE BACKTEST LAB")
    print("=" * 80)

    config = BacktestConfig(
        backtest_id="bt-institutional-01",
        symbols=["AAPL", "NVDA", "MSFT", "SPY"],
        initial_cash=100000.0,
        slippage_bps=5.0,
        commission_per_share=0.005,
        strategies_enabled=["trend_following", "momentum", "breakout", "statistical_arbitrage"],
    )

    result = await backtest_engine.run_backtest(config)
    m = result.metrics

    print(f"\n--- PERFORMANCE METRICS ({config.backtest_id}) ---")
    print(f"Total Return:       {m.total_return_pct*100:+.2f}%")
    print(f"CAGR:               {m.cagr*100:.2f}%")
    print(f"Sharpe Ratio:       {m.sharpe_ratio:.2f}")
    print(f"Sortino Ratio:      {m.sortino_ratio:.2f}")
    print(f"Calmar Ratio:       {m.calmar_ratio:.2f}")
    print(f"Max Drawdown:       {m.max_drawdown_pct*100:.2f}%")
    print(f"Win Rate:           {m.win_rate*100:.1f}% ({m.winning_trades} wins / {m.total_trades} trades)")
    print(f"Profit Factor:      {m.profit_factor:.2f}")
    print(f"Expectancy:         ${m.expectancy:,.2f} per trade")
    print(f"1-Day 95% VaR:      {m.var_95*100:.2f}%")
    print(f"1-Day 95% CVaR:     {m.cvar_95*100:.2f}%")

    if result.monte_carlo:
        mc = result.monte_carlo
        print("\n--- MONTE CARLO ANALYSIS (1,000 SIMULATED PATHS) ---")
        print(f"Median CAGR:        {mc.median_cagr*100:.2f}%")
        print(f"5th Percentile:     {mc.percentile_5th_cagr*100:.2f}%")
        print(f"95th Percentile:    {mc.percentile_95th_cagr*100:.2f}%")
        print(f"Median Max DD:      {mc.median_max_drawdown*100:.2f}%")
        print(f"Probability Ruin:   {mc.probability_of_ruin*100:.4f}%")


if __name__ == "__main__":
    asyncio.run(main())
