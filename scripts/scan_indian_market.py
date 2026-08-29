"""
ATHENA Indian Market Scanner & Quantitative Multi-Agent Asset Selector
Scans top NSE large-cap & growth leaders across Technical, Fundamental, Quant Alpha,
Sentiment, Macro, and 16 Quantitative Strategies to select the top opportunities.
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

from packages.database.session import init_db
from packages.schemas.agent import AgentContext
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.debate_service.engine import debate_engine
from services.decision_service.engine import decision_engine
from services.feature_service.pipeline import feature_pipeline
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector
from services.strategy_service.registry import strategy_registry

INDIAN_UNIVERSE = [
    ("RELIANCE", "Reliance Industries", "Energy / Telecom / Retail"),
    ("TCS", "Tata Consultancy Services", "IT & Digital Transformation"),
    ("HDFCBANK", "HDFC Bank", "Private Banking & Financials"),
    ("INFY", "Infosys", "IT Services & Generative AI"),
    ("ICICIBANK", "ICICI Bank", "Banking & Credit Growth"),
    ("TATAMOTORS", "Tata Motors", "Automotive & EV Mobility"),
    ("BHARTIARTL", "Bharti Airtel", "Telecom & 5G Infrastructure"),
    ("LT", "Larsen & Toubro", "Infrastructure & Capital Goods"),
    ("ITC", "ITC Limited", "FMCG & Agri-Business"),
    ("SBIN", "State Bank of India", "Public Sector Banking"),
]


async def analyze_indian_universe():
    await init_db()
    print("=" * 95)
    print("  ATHENA QUANTITATIVE OS - INDIAN NSE MULTI-AGENT MARKET SCANNER")
    print("=" * 95)

    results = []

    # 1. Macro Regime Check on NIFTY 50 Benchmark
    nifty_candles = await data_pipeline.ingest_candles("NIFTY50", limit=200)
    nifty_features = feature_pipeline.compute_features("NIFTY50", nifty_candles)
    nifty_regime = regime_detector.detect_regime(nifty_features)
    print(f"\n[BENCHMARK] NIFTY 50 Regime: {nifty_regime.regime.value} (Confidence: {nifty_regime.confidence*100:.0f}%)")
    print(f"            RSI(14): {nifty_features.technical.rsi_14:.1f} | 20D Realized Vol: {nifty_features.volatility.realized_vol_20d*100:.1f}%\n")

    print("-" * 95)
    print(f"{'SYMBOL':<12} {'PRICE (INR)':<14} {'ACTION':<8} {'CONSENSUS':<11} {'AGREEMENT':<11} {'R:R':<6} {'EXP RETURN':<12} {'TOP CATALYST'}")
    print("-" * 95)

    for sym, name, sector in INDIAN_UNIVERSE:
        try:
            candles = await data_pipeline.ingest_candles(sym, limit=200)
            features = feature_pipeline.compute_features(sym, candles)
            regime = regime_detector.detect_regime(features)

            ctx = AgentContext(
                symbol=sym,
                feature_snapshot=features,
                regime_state=regime,
            )

            agents_summary = await agent_orchestrator.run_all_agents(ctx)
            strat_outputs = strategy_registry.run_all_strategies(ctx)
            debate = debate_engine.conduct_debate(sym, agents_summary, strat_outputs)

            port_state = portfolio_manager.get_portfolio_state()
            decision = decision_engine.generate_decision(
                symbol=sym,
                feature_snapshot=features,
                regime_state=regime,
                agent_summary=agents_summary,
                strategy_outputs=strat_outputs,
                debate_report=debate,
                portfolio_state=port_state,
            )

            # Driver extraction
            primary_driver = debate.strongest_bullish_evidence[0] if debate.strongest_bullish_evidence else "Momentum breakout"
            if len(primary_driver) > 30:
                primary_driver = primary_driver[:27] + "..."

            cur_px = candles[-1].close
            score = (agents_summary.aggregate_confidence * 0.40) + (debate.agreement_score * 0.35) + (min(decision.risk_reward_ratio / 3.0, 1.0) * 0.25)

            results.append({
                "symbol": sym,
                "name": name,
                "sector": sector,
                "price": cur_px,
                "action": decision.action.value,
                "confidence": agents_summary.aggregate_confidence,
                "agreement": debate.agreement_score,
                "rr": decision.risk_reward_ratio,
                "exp_return": decision.expected_return_pct,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "driver": primary_driver,
                "score": score,
                "bull_count": len(agents_summary.supporting_agents),
                "bear_count": len(agents_summary.opposing_agents),
            })

            print(f"{sym:<12} Rs. {cur_px:<10,.2f} {decision.action.value:<8} {agents_summary.aggregate_confidence*100:>3.0f}%        {debate.agreement_score:>4.2f}        {decision.risk_reward_ratio:>3.1f}:1  +{decision.expected_return_pct*100:>4.1f}%       {primary_driver}")

        except Exception as e:
            print(f"{sym:<12} Error: {e}")

    # Rank by composite multi-agent score
    results.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "=" * 95)
    print("  TOP CONVICTION PICKS SELECTED BY ATHENA AI AGENTS & QUANT STRATEGIES")
    print("=" * 95)

    for rank, item in enumerate(results[:4], start=1):
        print(f"\n#{rank} [{item['symbol']}] {item['name']} - {item['sector']}")
        print(f"   - Current Price: Rs. {item['price']:,.2f} | Action: {item['action']} (Confidence: {item['confidence']*100:.0f}%)")
        print(f"   - Consensus: {item['bull_count']} Supporting AI Agents vs {item['bear_count']} Opposing (Agreement: {item['agreement']*100:.0f}%)")
        print(f"   - Target Sizing & Levels: Stop Loss: Rs. {item['stop_loss']:,.2f} | Target: Rs. {item['take_profit']:,.2f} | R:R: {item['rr']:.1f}:1")
        print(f"   - Core Thesis: {item['driver']}")

    print("\n" + "=" * 95)


if __name__ == "__main__":
    asyncio.run(analyze_indian_universe())
