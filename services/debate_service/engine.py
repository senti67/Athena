"""
ATHENA Correlation-Aware Signal Aggregator & Dialectical Debate Engine
Aggregates analytical modules and strategy signals across orthogonal feature groups:
TREND, MOMENTUM, MEAN_REVERSION, VOLATILITY, FUNDAMENTAL, SENTIMENT, MACRO, REGIME.
Deduplicates correlated indicators and applies regime-weighted synthesis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from packages.common.config import settings
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentOutput, AgentRunSummary, AgentSignalType, FeatureGroup
from packages.schemas.debate import ConflictItem, DebateReport
from packages.schemas.events import Event, EventType
from packages.schemas.regime import RegimeState
from packages.schemas.strategy import StrategyOutput, StrategySignal

logger = get_logger("athena.debate_engine")


class SignalAggregator:
    """
    Correlation-Aware Signal Aggregation Engine.
    Aggregates inputs by orthogonal feature groups to prevent correlated indicator dominance.
    """

    BASE_GROUP_WEIGHTS: Dict[str, float] = {
        "trend": 0.25,
        "momentum": 0.20,
        "mean_reversion": 0.15,
        "volatility": 0.15,
        "fundamental": 0.10,
        "sentiment": 0.05,
        "macro": 0.10,
        "regime": 0.00,  # Used for regime multiplier rather than standalone vote
    }

    def aggregate_signals(
        self,
        symbol: str,
        agent_summary: AgentRunSummary,
        strategy_outputs: Dict[str, StrategyOutput],
        regime_state: Optional[RegimeState] = None,
    ) -> DebateReport:
        # 1. Bucket all outputs by FeatureGroup
        group_signals: Dict[str, List[float]] = {k: [] for k in self.BASE_GROUP_WEIGHTS}
        group_confidences: Dict[str, List[float]] = {k: [] for k in self.BASE_GROUP_WEIGHTS}
        group_qualities: Dict[str, List[float]] = {k: [] for k in self.BASE_GROUP_WEIGHTS}
        group_evidence: Dict[str, List[str]] = {k: [] for k in self.BASE_GROUP_WEIGHTS}

        unavailable_domains: List[str] = list(agent_summary.unavailable_agents)
        bullish_points: List[str] = []
        bearish_points: List[str] = []
        weakest_evidence: List[str] = []

        # Process Analytical Modules
        for name, out in agent_summary.agent_outputs.items():
            if out.signal == AgentSignalType.UNAVAILABLE or out.data_quality == 0.0:
                if name not in unavailable_domains:
                    unavailable_domains.append(name)
                continue

            grp = out.feature_group.value if hasattr(out.feature_group, "value") else str(out.feature_group)
            if grp not in group_signals:
                grp = "trend"

            # Numerical signal: BUY = +1.0, SELL = -1.0, HOLD = 0.0
            sig_val = 1.0 if out.signal == AgentSignalType.BUY else (-1.0 if out.signal == AgentSignalType.SELL else 0.0)
            group_signals[grp].append(sig_val)
            group_confidences[grp].append(out.confidence)
            group_qualities[grp].append(out.data_quality)

            if out.bullish_points:
                bullish_points.extend([f"[{grp.upper()}] {p}" for p in out.bullish_points[:2]])
            if out.bearish_points:
                bearish_points.extend([f"[{grp.upper()}] {p}" for p in out.bearish_points[:2]])
            if out.confidence < 0.60:
                weakest_evidence.append(f"Low confidence ({out.confidence:.0%}) in {grp}")

        # Process Active Strategies
        for strat_name, strat_out in strategy_outputs.items():
            if not strat_out.is_active or strat_out.signal == StrategySignal.UNAVAILABLE:
                continue

            grp = strat_out.feature_group.value if hasattr(strat_out.feature_group, "value") else str(strat_out.feature_group)
            if grp not in group_signals:
                grp = "trend"

            sig_val = 1.0 if strat_out.signal == StrategySignal.BUY else (-1.0 if strat_out.signal == StrategySignal.SELL else 0.0)
            group_signals[grp].append(sig_val)
            group_confidences[grp].append(strat_out.confidence)
            group_qualities[grp].append(strat_out.data_quality)

            if strat_out.evidence:
                if strat_out.signal == StrategySignal.BUY:
                    bullish_points.extend([f"[STRAT-{strat_name}] {e}" for e in strat_out.evidence[:1]])
                elif strat_out.signal == StrategySignal.SELL:
                    bearish_points.extend([f"[STRAT-{strat_name}] {e}" for e in strat_out.evidence[:1]])

        # 2. Compute Normalized Score & Quality per Feature Group
        feature_group_scores: Dict[str, float] = {}
        feature_group_confidences: Dict[str, float] = {}
        feature_group_qualities: Dict[str, float] = {}

        for grp in self.BASE_GROUP_WEIGHTS:
            sigs = group_signals[grp]
            confs = group_confidences[grp]
            quals = group_qualities[grp]

            if not sigs or sum(confs) == 0:
                feature_group_scores[grp] = 0.0
                feature_group_confidences[grp] = 0.0
                feature_group_qualities[grp] = 0.0
            else:
                # Weighted average signal for this group
                weighted_sig = sum(s * c for s, c in zip(sigs, confs)) / sum(confs)
                avg_conf = sum(confs) / len(confs)
                avg_qual = sum(quals) / len(quals)

                feature_group_scores[grp] = round(weighted_sig, 3)
                feature_group_confidences[grp] = round(avg_conf, 3)
                feature_group_qualities[grp] = round(avg_qual, 3)

        # 3. Apply Regime Suitability Weights
        regime_weights = {}
        if regime_state and regime_state.feature_group_weights:
            regime_weights = regime_state.feature_group_weights

        total_weight = 0.0
        weighted_score_sum = 0.0
        weighted_conf_sum = 0.0

        for grp, base_w in self.BASE_GROUP_WEIGHTS.items():
            if base_w <= 0.0:
                continue

            # Only weight groups that have active data quality
            qual = feature_group_qualities.get(grp, 0.0)
            if qual <= 0.0:
                continue

            regime_mult = regime_weights.get(grp, 1.0)
            effective_weight = base_w * regime_mult * qual

            score = feature_group_scores.get(grp, 0.0)
            conf = feature_group_confidences.get(grp, 0.50)

            weighted_score_sum += score * effective_weight
            weighted_conf_sum += conf * effective_weight
            total_weight += effective_weight

        composite_score = round(weighted_score_sum / total_weight, 3) if total_weight > 0 else 0.0
        raw_confidence = round(weighted_conf_sum / total_weight, 3) if total_weight > 0 else 0.50

        # 4. Detect Cross-Domain Conflicts and Calculate Penalty
        conflicts: List[ConflictItem] = []
        conflict_penalty = 0.0

        # Check Trend vs Mean Reversion conflict
        trend_score = feature_group_scores.get("trend", 0.0)
        meanrev_score = feature_group_scores.get("mean_reversion", 0.0)
        if trend_score > 0.4 and meanrev_score < -0.4:
            conflicts.append(
                ConflictItem(
                    agents_involved=["trend", "mean_reversion"],
                    topic="Trend Momentum vs Mean Reversion Overextension",
                    agent_a_position="Trend confirms bullish continuation",
                    agent_b_position="Mean reversion warns of overbought resistance",
                    severity=0.60,
                    resolution="Proceed with tighter ATR trailing stop loss.",
                )
            )
            conflict_penalty += 0.10

        elif trend_score < -0.4 and meanrev_score > 0.4:
            conflicts.append(
                ConflictItem(
                    agents_involved=["trend", "mean_reversion"],
                    topic="Downtrend Breakdown vs Oversold Bounce",
                    agent_a_position="Trend indicates strong downward momentum",
                    agent_b_position="Mean reversion detects oversold dip",
                    severity=0.65,
                    resolution="Await trend reversal confirmation before initiating longs.",
                )
            )
            conflict_penalty += 0.12

        # Check Macro vs Technical
        macro_score = feature_group_scores.get("macro", 0.0)
        if macro_score < -0.3 and trend_score > 0.4:
            conflicts.append(
                ConflictItem(
                    agents_involved=["macro", "trend"],
                    topic="Macro Risk-Off vs Single-Stock Momentum",
                    agent_a_position="Macro warns of broad market risk-off / elevated VIX",
                    agent_b_position="Stock technicals show bullish breakout",
                    severity=0.50,
                    resolution="Scale down position size to reduce portfolio market beta.",
                )
            )
            conflict_penalty += 0.08

        # Apply conflict penalty to confidence
        calibrated_confidence = round(max(0.30, raw_confidence * (1.0 - min(0.35, conflict_penalty))), 2)

        # 5. Agreement & Consensus Counts
        bull_groups = sum(1 for s in feature_group_scores.values() if s >= 0.25)
        bear_groups = sum(1 for s in feature_group_scores.values() if s <= -0.25)
        neutral_groups = len(feature_group_scores) - (bull_groups + bear_groups)
        active_domains = sum(1 for q in feature_group_qualities.values() if q > 0)

        agreement_score = round(max(bull_groups, bear_groups) / max(1, active_domains), 2)
        domain_diversity = round(active_domains / len(self.BASE_GROUP_WEIGHTS), 2)

        # 6. Directional Recommendation & Expected Edge
        min_signal = getattr(settings, "ATHENA_MIN_SIGNAL_SCORE", 0.55)
        min_conf = getattr(settings, "MIN_RESEARCH_CONFIDENCE", 0.60)
        min_agr = getattr(settings, "MIN_RESEARCH_AGREEMENT", 0.60)

        expected_edge = round(composite_score * 0.045, 4)

        if composite_score >= min_signal and calibrated_confidence >= min_conf and agreement_score >= min_agr:
            recommended_action = "BUY"
            synthesis = (
                f"Correlation-Aware Aggregator confirms a BUY stance on {symbol} (Score: +{composite_score:.2f}, "
                f"Confidence: {calibrated_confidence:.0%}, Agreement: {agreement_score:.0%}). "
                f"Leading groups: Trend={trend_score:+.2f}, Momentum={feature_group_scores.get('momentum', 0):+.2f}."
            )
        elif composite_score <= -min_signal and calibrated_confidence >= min_conf and agreement_score >= min_agr:
            recommended_action = "SELL"
            synthesis = (
                f"Correlation-Aware Aggregator confirms a SELL stance on {symbol} (Score: {composite_score:.2f}, "
                f"Confidence: {calibrated_confidence:.0%}, Agreement: {agreement_score:.0%})."
            )
        else:
            recommended_action = "HOLD"
            synthesis = (
                f"Aggregator recommends HOLD on {symbol} (Score: {composite_score:+.2f} below threshold ±{min_signal:.2f} "
                f"or Agreement: {agreement_score:.0%} < {min_agr:.0%}). Preserving capital."
            )

        report = DebateReport(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            agreement_score=agreement_score,
            composite_score=composite_score,
            expected_edge=expected_edge,
            conflict_penalty=round(conflict_penalty, 2),
            feature_group_scores=feature_group_scores,
            conflicts=conflicts,
            strongest_bullish_evidence=bullish_points[:5],
            strongest_bearish_evidence=bearish_points[:5],
            weakest_evidence=weakest_evidence[:3],
            missing_information=[f"Unavailable data: {u}" for u in unavailable_domains],
            bull_count=bull_groups,
            bear_count=bear_groups,
            neutral_count=neutral_groups,
            unavailable_count=len(unavailable_domains),
            domain_diversity_score=domain_diversity,
            debate_synthesis=synthesis,
            recommended_action=recommended_action,
            consensus_confidence=calibrated_confidence,
        )

        return report


class DebateEngine:
    """Interfacing debate synthesizer that delegates to SignalAggregator."""

    def __init__(self):
        self.aggregator = SignalAggregator()

    def conduct_debate(
        self,
        symbol: str,
        agent_summary: AgentRunSummary,
        strategy_outputs: Dict[str, StrategyOutput],
        regime_state: Optional[RegimeState] = None,
    ) -> DebateReport:
        return self.aggregator.aggregate_signals(
            symbol=symbol,
            agent_summary=agent_summary,
            strategy_outputs=strategy_outputs,
            regime_state=regime_state,
        )


debate_engine = DebateEngine()
ResearchConsensusEngine = DebateEngine
research_consensus_engine = debate_engine
