"""
ATHENA Event-Driven Quantitative Backtest & Strategy Diagnostic Runner
"""

import argparse
import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.schemas.backtest import BacktestConfig
from services.backtest_service.engine import backtest_engine
from services.backtest_service.performance_analyzer import performance_analyzer


async def main():
    parser = argparse.ArgumentParser(description="Run Athena Quantitative Backtest Lab")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "NVDA", "MSFT", "JNJ", "SPY"], help="Symbols to backtest")
    parser.add_argument("--cash", type=float, default=100000.0, help="Initial cash balance")
    parser.add_argument("--slippage", type=float, default=5.0, help="Slippage in basis points")
    args = parser.parse_args()

    config = BacktestConfig(
        backtest_id=f"bt-quant-{len(args.symbols)}assets",
        symbols=args.symbols,
        initial_cash=args.cash,
        slippage_bps=args.slippage,
        commission_per_share=0.005,
        strategies_enabled=["trend_following", "momentum", "mean_reversion", "breakout", "pullback", "volatility_swing"],
    )

    result = await backtest_engine.run_backtest(config)
    report_text = performance_analyzer.generate_diagnostic_report(result)
    print(report_text)


if __name__ == "__main__":
    asyncio.run(main())
