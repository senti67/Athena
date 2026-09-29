"""
ATHENA Autonomous Alpaca Paper Trading Engine
Directly interfaces with Alpaca Paper API (https://paper-api.alpaca.markets/v2).
Executes trades autonomously to your official Alpaca account.
"""

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
from services.strategy_service.engine import strategy_engine
from services.strategy_service.registry import strategy_registry


async def run_alpaca_pipeline(symbol: str = "AAPL"):
    print("=" * 85)
    print("  ATHENA QUANTITATIVE OS - AUTONOMOUS ALPACA PAPER TRADING")
    print(f"  Target Endpoint: {settings.ALPACA_BASE_URL}/v2")
    print("=" * 85)

    has_real_keys = (
        bool(settings.ALPACA_API_KEY)
        and settings.ALPACA_API_KEY != "your_alpaca_api_key_id"
        and not settings.ALPACA_API_KEY.startswith("PK_MOCK")
    )

    # 0. Initialize DB & Sync Alpaca Account
    await init_db()
    print("\n[Step 0] Synchronizing with Alpaca Paper Trading Account...")
    acct = await alpaca_broker.get_account()
    equity = float(acct.get("equity", 100000.0))
    cash = float(acct.get("cash", 100000.0))
    buying_power = float(acct.get("buying_power", 200000.0))
    print(f"[OK] Connected to Alpaca Account: {acct.get('account_number', 'PAPER-ACTIVE')} | Status: {acct.get('status', 'ACTIVE')}")
    print(f"     Equity: ${equity:,.2f} | Cash: ${cash:,.2f} | Buying Power: ${buying_power:,.2f}")

    alpaca_positions = await alpaca_broker.get_positions()
    open_orders = await alpaca_broker.get_open_orders()
    portfolio_manager.sync_from_alpaca(acct, alpaca_positions)
    print(f"[OK] Current Open Positions on Alpaca: {len(alpaca_positions)} | Active Queued Orders: {len(open_orders)}")
    for pos in alpaca_positions:
        print(f"     - [Position] {pos.get('symbol')}: {pos.get('qty')} shares @ avg ${float(pos.get('avg_entry_price', 0)):,.2f} (Current: ${float(pos.get('current_price', 0)):,.2f})")

    symbol_upper = symbol.upper()
    existing_queued_symbols = [o.get("symbol", "").upper() for o in open_orders]
    existing_position_symbols = [p.get("symbol", "").upper() for p in alpaca_positions]

    if symbol_upper in existing_queued_symbols or symbol_upper in existing_position_symbols:
        print(f"\n[HOLD] Asset {symbol_upper} already has an active position / queued order on Alpaca.")
        print(f"       Preserving capital and preventing duplicate re-buying. (No new order placed)")
        print("=" * 85)
        return

    # 1. Ingest Market Data
    print(f"\n[Step 1] Ingesting Real-Time Market Data for {symbol} & Evaluating Quality...")
    candles = await data_pipeline.ingest_candles(symbol, limit=200)
    latest_candle = candles[-1]
    print(f"[OK] Retrieved {len(candles)} bars for {symbol}. Latest Close: ${latest_candle.close:,.2f}")

    # 2. Extract Quantitative Features
    print("\n[Step 2] Calculating Quantitative Feature Matrix...")
    features = feature_pipeline.compute_features(symbol, candles)
    print(f"[OK] RSI(14): {features.technical.rsi_14:.1f} | MACD Hist: {features.technical.macd_hist:+.3f} | Realized Vol: {features.volatility.realized_vol_20d*100:.1f}%")

    # 3. Market Regime Detection
    print("\n[Step 3] Detecting Market Regime Classifier...")
    regime = regime_detector.detect_regime(features)
    print(f"[OK] Detected Regime: {regime.regime.value} (Confidence: {regime.confidence*100:.0f}%)")

    # 4. Run 8 Quantitative Analytical Modules
    print("\n[Step 4] Running 8 Quantitative Analytical Modules in Parallel...")
    portfolio_state = portfolio_manager.get_portfolio_state()
    try:
        fundamentals = await asyncio.wait_for(data_pipeline.get_fundamental_metrics(symbol), timeout=2.5)
    except Exception:
        fundamentals = {}

    try:
        news = await asyncio.wait_for(data_pipeline.get_company_news(symbol, limit=5), timeout=2.0)
    except Exception:
        news = []

    agent_context = AgentContext(
        symbol=symbol,
        feature_snapshot=features,
        regime_state=regime,
        portfolio_cash=cash,
        fundamental_metrics=fundamentals if isinstance(fundamentals, dict) else {},
        market_news=news if isinstance(news, list) else [],
    )
    agents_summary = await agent_orchestrator.run_all_agents(agent_context)
    print(f"[OK] 8 Modules Completed: Supporting: {len(agents_summary.supporting_agents)} | Opposing: {len(agents_summary.opposing_agents)} | Consensus Conf: {agents_summary.aggregate_confidence*100:.0f}%")

    # 5. Evaluate 6 Active Quantitative Strategies
    print("\n[Step 5] Evaluating Active Quantitative Strategies...")
    best_strat_setup, strategy_outputs = strategy_engine.evaluate_strategies(agent_context)
    buy_strats = [k for k, v in strategy_outputs.items() if v.signal.value == "BUY"]
    print(f"[OK] Active Buy Setups ({len(buy_strats)}): {', '.join(buy_strats) if buy_strats else 'None qualified'}...")

    # 6. Correlation-Aware Signal Aggregator
    print("\n[Step 6] Aggregating Signals Across Orthogonal Feature Groups...")
    debate_report = debate_engine.conduct_debate(symbol, agents_summary, strategy_outputs, regime)
    print(f"[OK] Aggregator Outcome: {debate_report.recommended_action} (Composite Score: {debate_report.composite_score:+.2f}, Confidence: {debate_report.consensus_confidence*100:.0f}%, Agreement: {debate_report.agreement_score:.2f})")

    # 7. Decision Synthesis & Expected Edge
    print("\n[Step 7] Generating Structured Decision with Expected Edge & Dynamic ATR Exits...")
    decision = decision_engine.generate_decision(
        symbol=symbol,
        feature_snapshot=features,
        regime_state=regime,
        agent_summary=agents_summary,
        strategy_outputs=strategy_outputs,
        debate_report=debate_report,
        portfolio_state=portfolio_state,
        best_strategy_setup=best_strat_setup,
    )
    print(f"[OK] Decision Stance: {decision.action.value} | Sizing: {decision.suggested_shares} shares @ ~${decision.current_price:,.2f}")
    print(f"     Expected Edge: {decision.expected_edge*100:+.2f}% | Stop Loss: ${decision.stop_loss:,.2f} | Take Profit: ${decision.take_profit:,.2f} (R:R = {decision.risk_reward_ratio:.1f}:1)")

    # 8. Risk VETO Layer Verification
    print("\n[Step 8] Passing Decision through Independent Risk Management VETO Layer...")
    risk_result = risk_engine.evaluate_decision(decision, portfolio_state)
    if not risk_result.approved:
        print(f"[X] RISK VETOED! Order blocked: {risk_result.veto_reason}")
        return
    print(f"[OK] RISK APPROVED! (Risk Score: {risk_result.risk_score:.2f}, Max Approved Shares: {risk_result.max_approved_shares})")

    if decision.action.value == "BUY" and risk_result.max_approved_shares > 0:
        # 9. Submit Order Directly to Alpaca Paper Trading
        print(f"\n[Step 9] Submitting Order to Alpaca Paper API ({settings.ALPACA_BASE_URL}/v2/orders)...")
        order_response = await execution_router.execute_trade(decision, risk_result, mode=ExecutionMode.PAPER)
        if order_response:
            print(f"[OK] Order Successfully Dispatched to Alpaca!")
            print(f"     Alpaca Order ID: {order_response.order_id}")
            print(f"     Status: {order_response.status.value}")
            if order_response.fills:
                fill = order_response.fills[0]
                print(f"     Fill Execution: {fill.quantity} shares of {symbol} @ ${fill.price:,.2f}")

            # 10. Record in Trade Journal
            print("\n[Step 10] Recording Complete Trade Audit in Journal...")
            journal_entry = journal_service.record_entry(decision, risk_result, order_response)
            print(f"[OK] Trade Journal Entry Created: ID {journal_entry.trade_id}")

    print("\n" + "=" * 85)
    print("  ATHENA ANALYSIS CYCLE COMPLETED")
    print("  View live paper account at: https://app.alpaca.markets/paper/dashboard/overview")
    print("=" * 85)


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    asyncio.run(run_alpaca_pipeline(sym))
