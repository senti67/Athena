"""
ATHENA Autonomous Indian Market Daily Quantitative Bot
Automates daily market scanning, multi-agent evaluation, risk checks,
autonomous trade execution, and trailing stop-loss / take-profit management.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.common.config import settings
from packages.database.session import init_db
from packages.schemas.agent import AgentContext
from packages.schemas.order import ExecutionMode
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.debate_service.engine import debate_engine
from services.decision_service.engine import decision_engine
from services.execution_service.alpaca_broker import alpaca_broker
from services.execution_service.router import execution_router
from services.feature_service.pipeline import feature_pipeline
from services.journal_service.journal import journal_service
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector
from services.risk_service.engine import risk_engine
from services.strategy_service.registry import strategy_registry

# Top Indian NSE Universe
INDIAN_STOCKS = [
    ("ICICIBANK", "ICICI Bank"),
    ("HDFCBANK", "HDFC Bank"),
    ("BHARTIARTL", "Bharti Airtel"),
    ("TCS", "Tata Consultancy Services"),
    ("RELIANCE", "Reliance Industries"),
    ("TATAMOTORS", "Tata Motors"),
    ("LT", "Larsen & Toubro"),
    ("ITC", "ITC Limited"),
    ("SBIN", "State Bank of India"),
    ("INFY", "Infosys"),
]


class IndianMarketDailyBot:
    """
    Institutional Autonomous Daily Scanner & Execution Bot.
    """

    def __init__(self, top_n_picks: int = 3, max_allocation_per_stock: float = 15000.0):
        self.top_n_picks = top_n_picks
        self.max_allocation_per_stock = max_allocation_per_stock

    async def run_daily_scan_and_trade(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 95)
        print(f"  🇮🇳 ATHENA DAILY INDIAN MARKET SCANNER ACTIVATED: {now_str}")
        print("=" * 95)

        await init_db()

        # Step 1: Benchmark Regime Health
        print("\n[Step 1] Evaluating NIFTY 50 Macro Regime...")
        nifty_candles = await data_pipeline.ingest_candles("NIFTY50", limit=200)
        nifty_features = feature_pipeline.compute_features("NIFTY50", nifty_candles)
        nifty_regime = regime_detector.detect_regime(nifty_features)
        print(f"[OK] Macro Regime: {nifty_regime.regime.value} (Confidence: {nifty_regime.confidence*100:.0f}%)")

        # Step 2: Multi-Agent Analysis across Universe
        print(f"\n[Step 2] Scanning {len(INDIAN_STOCKS)} Indian Assets with 14 AI Agents & 16 Quant Strategies...")
        scored_candidates = []

        for symbol, name in INDIAN_STOCKS:
            try:
                candles = await data_pipeline.ingest_candles(symbol, limit=200)
                features = feature_pipeline.compute_features(symbol, candles)
                regime = regime_detector.detect_regime(features)

                ctx = AgentContext(
                    symbol=symbol,
                    feature_snapshot=features,
                    regime_state=regime,
                )

                agents_summary = await agent_orchestrator.run_all_agents(ctx)
                strat_outputs = strategy_registry.run_all_strategies(ctx)
                debate = debate_engine.conduct_debate(symbol, agents_summary, strat_outputs)

                port_state = portfolio_manager.get_portfolio_state()
                decision = decision_engine.generate_decision(
                    symbol=symbol,
                    feature_snapshot=features,
                    regime_state=regime,
                    agent_summary=agents_summary,
                    strategy_outputs=strat_outputs,
                    debate_report=debate,
                    portfolio_state=port_state,
                )

                if decision.action.value == "BUY":
                    composite_score = (
                        agents_summary.aggregate_confidence * 0.40
                        + debate.agreement_score * 0.35
                        + min(decision.risk_reward_ratio / 3.0, 1.0) * 0.25
                    )
                    scored_candidates.append({
                        "symbol": symbol,
                        "name": name,
                        "decision": decision,
                        "debate": debate,
                        "price": candles[-1].close,
                        "score": composite_score,
                        "confidence": agents_summary.aggregate_confidence,
                        "agreement": debate.agreement_score,
                    })

            except Exception as e:
                print(f"[!] Error scanning {symbol}: {e}")

        # Step 3: Rank & Select Top Opportunities
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_picks = scored_candidates[: self.top_n_picks]

        print(f"\n[Step 3] Selected Top {len(top_picks)} High-Conviction Opportunities for Execution:")
        for idx, pick in enumerate(top_picks, 1):
            print(f"  {idx}. {pick['symbol']} ({pick['name']}) - Price: Rs. {pick['price']:,.2f} | Score: {pick['score']:.2f} | Conf: {pick['confidence']*100:.0f}%")

        # Step 4: Risk VETO and Autonomous Execution
        print("\n[Step 4] Processing Orders through Risk Management VETO Layer...")
        executed_orders = []

        for pick in top_picks:
            sym = pick["symbol"]
            dec = pick["decision"]
            port_state = portfolio_manager.get_portfolio_state()

            # Dynamic position sizing within 15% institutional cap
            shares = max(1, int(self.max_allocation_per_stock / max(pick["price"], 1.0)))
            dec.suggested_shares = shares

            risk_result = risk_engine.evaluate_decision(dec, port_state)
            if not risk_result.approved:
                print(f"[X] {sym} VETOED by Risk: {risk_result.veto_reason}")
                continue

            print(f"[OK] RISK APPROVED for {sym}! Executing BUY {risk_result.max_approved_shares} shares...")
            try:
                order_response = await execution_router.execute_trade(
                    dec, risk_result, mode=ExecutionMode.PAPER
                )
                if order_response:
                    executed_orders.append((sym, order_response, dec))
                    journal_service.record_entry(dec, risk_result, order_response)
                    print(f"     [+] ORDER FILLED: {sym} (Order ID: {order_response.order_id})")
            except Exception as ex:
                print(f"     [!] Execution error for {sym}: {ex}")

        # Step 5: Daily Summary Report
        port = portfolio_manager.get_portfolio_state()
        print("\n" + "=" * 95)
        print("  📊 DAILY AUTONOMOUS RUN SUMMARY:")
        print(f"  Total Trades Executed Today: {len(executed_orders)}")
        print(f"  Portfolio NAV: Rs. {port.nav:,.2f} | Available Cash: Rs. {port.cash:,.2f}")
        print(f"  Active Positions in Portfolio: {len(port.positions)}")
        for sym, pos in port.positions.items():
            print(f"    - {sym}: {pos.shares:.0f} shares @ Rs. {pos.average_entry_price:,.2f} (Current: Rs. {pos.current_price:,.2f} | Unrealized P&L: Rs. {pos.unrealized_pnl:+,.2f})")
        print("=" * 95)


async def start_daily_automation_loop(interval_hours: int = 24, run_immediately: bool = True):
    bot = IndianMarketDailyBot(top_n_picks=3, max_allocation_per_stock=15000.0)
    print("=" * 95)
    print("  🚀 ATHENA DAILY INDIAN MARKET AUTONOMOUS BOT STARTED")
    print(f"  Schedule: Every {interval_hours} hours (Market Open / Daily Cycle)")
    print("  Press Ctrl + C anytime to stop.")
    print("=" * 95)

    if run_immediately:
        print("\n>>> Running initial daily scan immediately... <<<")
        await bot.run_daily_scan_and_trade()

    while True:
        next_run = datetime.now() + timedelta(hours=interval_hours)
        print(f"\n[Sleeping] Next automated market scan scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        await asyncio.sleep(interval_hours * 3600)
        await bot.run_daily_scan_and_trade()


if __name__ == "__main__":
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    try:
        asyncio.run(start_daily_automation_loop(interval_hours=hrs, run_immediately=True))
    except KeyboardInterrupt:
        print("\n[!] ATHENA Indian Market Daily Bot stopped by user.")
