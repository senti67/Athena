"""
ATHENA Autonomous Hedge Fund End-to-End Simulation Script
Demonstrates:
Data Ingestion -> Feature Extraction -> 14 AI Agents -> 16 Strategies ->
Dialectical Debate -> Statistical Evidence Validation -> Decision Engine ->
Independent Risk Veto Layer -> Paper Broker Execution -> Portfolio Update ->
Trade Journal & Explainability Report.
"""

import asyncio
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.database.session import init_db
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentContext
from packages.schemas.order import ExecutionMode
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.debate_service.engine import debate_engine
from services.decision_service.engine import decision_engine
from services.execution_service.router import execution_router
from services.feature_service.pipeline import feature_pipeline
from services.journal_service.journal import journal_service
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector
from services.risk_service.engine import risk_engine
from services.strategy_service.registry import strategy_registry

logger = get_logger("athena.simulation")


async def run_simulation(symbol: str = "AAPL"):
    print("=" * 80)
    print(f"  ATHENA QUANTITATIVE OPERATING SYSTEM - AUTONOMOUS SIMULATION: {symbol}")
    print("=" * 80)

    # 0. Initialize Database
    await init_db()

    # 1. Ingest Market Data & Run DQA
    print("\n[Step 1] Ingesting Market Data & Running Data Quality Agent...")
    candles = await data_pipeline.ingest_candles(symbol, limit=200)
    latest_candle = candles[-1]
    print(f"[OK] Ingested {len(candles)} daily bars for {symbol}. Latest Close: ${latest_candle.close:,.2f}")

    # 2. Extract Quantitative Features
    print("\n[Step 2] Calculating Multidimensional Quantitative Features...")
    features = feature_pipeline.compute_features(symbol, candles)
    print(f"[OK] RSI(14): {features.technical.rsi_14:.1f} | MACD Hist: {features.technical.macd_hist:+.3f} | Realized Vol: {features.volatility.realized_vol_20d*100:.1f}%")

    # 3. Market Regime Detection
    print("\n[Step 3] Detecting Market Regime with Multi-Model Ensemble...")
    regime = regime_detector.detect_regime(features)
    print(f"[OK] Detected Regime: {regime.regime.value} (Confidence: {regime.confidence*100:.0f}%)")
    print(f"  Description: {regime.description}")

    # 4. Run 14 AI Analytical Agents
    print("\n[Step 4] Running 14 Autonomous AI Analytical & Operational Agents in Parallel...")
    portfolio_state = portfolio_manager.get_portfolio_state()
    context = AgentContext(
        symbol=symbol,
        feature_snapshot=features,
        regime_state=regime,
        portfolio_cash=portfolio_state.cash,
    )
    agent_summary = await agent_orchestrator.run_all_agents(context)
    print(f"[OK] Agents complete! Supporting: {len(agent_summary.supporting_agents)} | Opposing: {len(agent_summary.opposing_agents)} | Avg Conf: {agent_summary.aggregate_confidence*100:.0f}%")
    for name, out in list(agent_summary.agent_outputs.items())[:5]:
        print(f"  - [{name.upper():<14}] Signal: {out.signal.value:<4} | Conf: {out.confidence*100:.0f}% | Latency: {out.latency_ms}ms")

    # 5. Run 16 Quantitative Strategies
    print("\n[Step 5] Evaluating 16 Independent Quantitative Trading Strategies...")
    strat_outputs = strategy_registry.run_all_strategies(context)
    buy_strats = [s for s, o in strat_outputs.items() if o.signal.value == "BUY"]
    print(f"[OK] Strategies complete! Active Buy Signals: {len(buy_strats)}/{len(strat_outputs)} ({', '.join(buy_strats[:4])}...)")

    # 6. Multi-Agent Dialectical Debate
    print("\n[Step 6] Synthesizing Multi-Agent Dialectical Debate & Conflict Analysis...")
    debate_report = debate_engine.conduct_debate(symbol, agent_summary, strat_outputs)
    print(f"[OK] Debate Outcome: {debate_report.recommended_action} (Consensus Conf: {debate_report.consensus_confidence*100:.0f}%, Agreement Score: {debate_report.agreement_score:.2f})")
    print(f"  Synthesis: {debate_report.debate_synthesis}")

    # 7. Confidence-Weighted Decision Engine & Evidence Validation
    print("\n[Step 7] Generating Structured Decision with Evidence Validation...")
    decision = decision_engine.generate_decision(
        symbol=symbol,
        feature_snapshot=features,
        regime_state=regime,
        agent_summary=agent_summary,
        strategy_outputs=strat_outputs,
        debate_report=debate_report,
        portfolio_state=portfolio_state,
    )
    print(f"[OK] Decision: {decision.action.value} | Suggested Size: {decision.suggested_shares} shares (${decision.suggested_shares * decision.current_price:,.2f})")
    print(f"  Stop Loss: ${decision.stop_loss:.2f} | Take Profit: ${decision.take_profit:.2f} (R:R {decision.risk_reward_ratio}:1)")

    # 8. Independent Risk Management Veto Layer
    print("\n[Step 8] Passing Decision through Independent Risk Management VETO Layer...")
    risk_check = risk_engine.evaluate_decision(decision, portfolio_state)
    if risk_check.approved:
        print(f"[OK] RISK APPROVED! Risk Score: {risk_check.risk_score:.2f} (Max Approved Shares: {risk_check.max_approved_shares})")
    else:
        print(f"[X] RISK VETOED! Reason: {risk_check.veto_reason}")

    # 9. Deterministic Order Construction & Paper Execution
    print("\n[Step 9] Executing Order via Deterministic Paper Broker...")
    order_response = await execution_router.execute_trade(decision, risk_check, mode=ExecutionMode.PAPER)
    if order_response:
        print(f"[OK] Order Executed: ID {order_response.order_id[:8]}... Status: {order_response.status.value}")
        for fill in order_response.fills:
            print(f"  -> Fill: {fill.quantity} shares @ ${fill.price:,.2f} (Slippage: {fill.slippage_bps:.1f} bps, Fee: ${fill.fee:.2f})")

        # 10. Trade Journaling & Explainability
        print("\n[Step 10] Recording Complete Trade Snapshot into Journal & Explainability Engine...")
        journal_entry = journal_service.record_entry(decision, risk_check, order_response)
        print(f"[OK] Journal Entry Created: ID {journal_entry.trade_id}")
        print("\n" + "-" * 40 + " TRADE EXPLAINABILITY REPORT " + "-" * 40)
        print(journal_entry.explainability_report_markdown)

    # 11. Final Portfolio State
    updated_state = portfolio_manager.get_portfolio_state()
    print("\n" + "=" * 80)
    print(f"  SIMULATION SUMMARY: NAV: ${updated_state.nav:,.2f} | Cash: ${updated_state.cash:,.2f} | Positions: {len(updated_state.positions)}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_simulation("AAPL"))
