"""
End-to-End Integration Tests for ATHENA Autonomous Trading Pipeline
"""

import pytest
from packages.database.session import init_db
from packages.schemas.agent import AgentContext
from packages.schemas.order import ExecutionMode, OrderStatus
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


@pytest.mark.asyncio
async def test_complete_autonomous_trading_pipeline():
    # 0. DB init
    await init_db()

    symbol = "AAPL"
    # 1. Ingest Data
    candles = await data_pipeline.ingest_candles(symbol, limit=100)
    assert len(candles) == 100

    # 2. Features
    features = feature_pipeline.compute_features(symbol, candles)
    assert features.current_price > 0

    # 3. Regime
    regime = regime_detector.detect_regime(features)
    assert regime.regime is not None

    # 4. Agents & Strategies
    port_state = portfolio_manager.get_portfolio_state()
    ctx = AgentContext(
        symbol=symbol,
        feature_snapshot=features,
        regime_state=regime,
        portfolio_cash=port_state.cash,
    )
    agents_summary = await agent_orchestrator.run_all_agents(ctx)
    strats = strategy_registry.run_all_strategies(ctx)

    # 5. Debate
    debate = debate_engine.conduct_debate(symbol, agents_summary, strats)
    assert debate.agreement_score >= 0.0

    # 6. Decision
    decision = decision_engine.generate_decision(
        symbol=symbol,
        feature_snapshot=features,
        regime_state=regime,
        agent_summary=agents_summary,
        strategy_outputs=strats,
        debate_report=debate,
        portfolio_state=port_state,
    )
    assert decision.action is not None

    # 7. Risk Veto Layer
    risk_check = risk_engine.evaluate_decision(decision, port_state)
    assert risk_check is not None

    # 8. Execution Router
    if risk_check.approved:
        order_resp = await execution_router.execute_trade(decision, risk_check, mode=ExecutionMode.PAPER)
        assert order_resp.status == OrderStatus.FILLED
        assert len(order_resp.fills) > 0

        # 9. Trade Journal
        entry = journal_service.record_entry(decision, risk_check, order_resp)
        assert entry.trade_id.startswith("TRD-")
        assert len(entry.explainability_report_markdown) > 50
