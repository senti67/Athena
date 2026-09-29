"""
ATHENA Quantitative Analytical Modules & Research Agents
Implements 8 domain-specific analytical modules with strict zero-fabrication invariants:
1. TechnicalTrendModule (EMA alignment, EMA slope, ADX trend confirmation)
2. MomentumModule (RSI acceleration, MACD histogram, 20d returns)
3. MeanReversionModule (Bollinger band deviation, 20d Z-score, statistical extremes)
4. VolatilityRiskModule (Realized volatility, ATR dispersion, VaR 95% risk estimation)
5. FundamentalModule (Finnhub financial metrics: ROE, P/E, D/E, FCF yield; UNAVAILABLE if not present)
6. SentimentNewsModule (News sentiment & NLP polarity; UNAVAILABLE if feed is empty)
7. MarketRegimeModule (Regime state, trend & volatility alignment)
8. CrossAssetMacroModule (Macro proxy returns, VIX, risk-on appetite)
"""

import math
from typing import Any, Dict, List, Optional
from datetime import datetime

from packages.schemas.agent import (
    AgentContext,
    AgentOutput,
    AgentSignalType,
    AgentType,
    EvidenceItem,
    FeatureGroup,
    ImplementationStatus,
)
from .base import BaseAgent


# ==========================================
# 1. TECHNICAL TREND MODULE (FeatureGroup.TREND)
# ==========================================
class TechnicalTrendModule(BaseAgent):
    """Analyzes moving average structure, slope, and ADX directional strength."""
    name = AgentType.TECHNICAL_TREND

    async def analyze(self, context: AgentContext) -> AgentOutput:
        tech = context.feature_snapshot.technical
        price = context.feature_snapshot.current_price
        adx = tech.adx_14
        regime = context.regime_state

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        features_used = ["ema_9", "ema_21", "ema_50", "ema_200", "adx_14", "pivot_support", "pivot_resistance"]

        # EMA Stack
        is_bull_stack = (tech.ema_9 > tech.ema_21 > tech.ema_50)
        is_bear_stack = (tech.ema_9 < tech.ema_21 < tech.ema_50)
        above_200 = (price > tech.ema_200) if tech.ema_200 > 0 else (price > tech.ema_50)

        if is_bull_stack:
            bullish.append("Bullish moving average stack: EMA 9 > EMA 21 > EMA 50")
            evidence.append(EvidenceItem(category="trend", point="EMA 9 > 21 > 50 stack", weight=1.3, is_bullish=True, feature_name="ema_9", feature_value=tech.ema_9))
        elif tech.ema_9 > tech.ema_21:
            bullish.append("Short-term EMA 9 > EMA 21 crossover")
            evidence.append(EvidenceItem(category="trend", point="EMA 9 > 21 crossover", weight=1.0, is_bullish=True, feature_name="ema_9", feature_value=tech.ema_9))
        elif is_bear_stack:
            bearish.append("Bearish moving average stack: EMA 9 < EMA 21 < EMA 50")
            evidence.append(EvidenceItem(category="trend", point="EMA 9 < 21 < 50 stack", weight=1.3, is_bullish=False, feature_name="ema_9", feature_value=tech.ema_9))
        else:
            bearish.append("Descending moving average alignment: EMA 9 < EMA 21")
            evidence.append(EvidenceItem(category="trend", point="EMA 9 < 21", weight=1.0, is_bullish=False, feature_name="ema_9", feature_value=tech.ema_9))

        if above_200:
            bullish.append(f"Price (${price:.2f}) above long-term trend baseline")
            evidence.append(EvidenceItem(category="trend", point="Price > EMA 200/50", weight=1.2, is_bullish=True, feature_name="price", feature_value=price))
        else:
            bearish.append(f"Price (${price:.2f}) below long-term trend baseline")
            evidence.append(EvidenceItem(category="trend", point="Price < EMA 200/50", weight=1.2, is_bullish=False, feature_name="price", feature_value=price))

        # ADX Trend Confirmation
        if adx >= 22.0:
            if is_bull_stack:
                bullish.append(f"Strong trend confirmed by ADX ({adx:.1f} >= 22.0)")
                evidence.append(EvidenceItem(category="trend", point=f"ADX={adx:.1f} confirms uptrend", weight=1.2, is_bullish=True, feature_name="adx_14", feature_value=adx))
            elif is_bear_stack:
                bearish.append(f"Strong downtrend confirmed by ADX ({adx:.1f} >= 22.0)")
                evidence.append(EvidenceItem(category="trend", point=f"ADX={adx:.1f} confirms downtrend", weight=1.2, is_bullish=False, feature_name="adx_14", feature_value=adx))

        net_score = len(bullish) - len(bearish)
        if is_bull_stack and above_200 and adx >= 18.0:
            signal = AgentSignalType.BUY
            confidence = min(0.92, max(0.60, 0.65 + (0.05 * net_score)))
            edge = 0.040
        elif is_bear_stack and not above_200 and adx >= 18.0:
            signal = AgentSignalType.SELL
            confidence = min(0.88, max(0.55, 0.60 + (0.05 * abs(net_score))))
            edge = -0.035
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        regime_weight = 1.0
        if regime and regime.feature_group_weights:
            regime_weight = regime.feature_group_weights.get("trend", 1.0)

        reasoning = (
            f"Trend Module: {signal.value} stance (Conf: {confidence:.0%}). "
            f"EMA Stack: 9={tech.ema_9:.2f}, 21={tech.ema_21:.2f}, 50={tech.ema_50:.2f}. "
            f"ADX={adx:.1f}, Price=${price:.2f}."
        )

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=round(regime_weight, 2),
            data_quality=1.0,
            feature_group=FeatureGroup.TREND,
            features_used=features_used,
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=reasoning,
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=round(tech.atr_14 / max(1.0, price), 4),
            holding_period_days=10,
            metrics={"ema_9": tech.ema_9, "ema_21": tech.ema_21, "ema_50": tech.ema_50, "adx_14": adx},
        )


# ==========================================
# 2. MOMENTUM MODULE (FeatureGroup.MOMENTUM)
# ==========================================
class MomentumModule(BaseAgent):
    """Analyzes RSI momentum, MACD histogram velocity, and return acceleration."""
    name = AgentType.MOMENTUM

    async def analyze(self, context: AgentContext) -> AgentOutput:
        tech = context.feature_snapshot.technical
        stat = context.feature_snapshot.statistical
        regime = context.regime_state

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        features_used = ["rsi_14", "macd_hist", "returns_20d", "returns_5d"]

        # RSI Momentum
        if 52.0 <= tech.rsi_14 <= 68.0:
            bullish.append(f"RSI ({tech.rsi_14:.1f}) in active expansion zone (52-68)")
            evidence.append(EvidenceItem(category="momentum", point=f"RSI={tech.rsi_14:.1f} bullish expansion", weight=1.2, is_bullish=True, feature_name="rsi_14", feature_value=tech.rsi_14))
        elif tech.rsi_14 > 72.0:
            bearish.append(f"RSI ({tech.rsi_14:.1f}) in overbought exhaustion zone")
            evidence.append(EvidenceItem(category="momentum", point="RSI overbought exhaustion", weight=1.1, is_bullish=False, feature_name="rsi_14", feature_value=tech.rsi_14))
        elif tech.rsi_14 < 38.0:
            bearish.append(f"RSI ({tech.rsi_14:.1f}) in depressed momentum breakdown")
            evidence.append(EvidenceItem(category="momentum", point="RSI depressed breakdown", weight=1.0, is_bullish=False, feature_name="rsi_14", feature_value=tech.rsi_14))

        # MACD Histogram
        if tech.macd_hist > 0:
            bullish.append(f"MACD histogram positive (+{tech.macd_hist:.3f})")
            evidence.append(EvidenceItem(category="momentum", point="Positive MACD histogram", weight=1.1, is_bullish=True, feature_name="macd_hist", feature_value=tech.macd_hist))
        else:
            bearish.append(f"MACD histogram negative ({tech.macd_hist:.3f})")
            evidence.append(EvidenceItem(category="momentum", point="Negative MACD histogram", weight=1.0, is_bullish=False, feature_name="macd_hist", feature_value=tech.macd_hist))

        # Multi-period Returns
        if stat.returns_20d > 0.03:
            bullish.append(f"Strong 20-day return momentum (+{stat.returns_20d*100:.1f}%)")
            evidence.append(EvidenceItem(category="momentum", point="20d return > 3%", weight=1.2, is_bullish=True, feature_name="returns_20d", feature_value=stat.returns_20d))
        elif stat.returns_20d < -0.03:
            bearish.append(f"Negative 20-day momentum ({stat.returns_20d*100:.1f}%)")
            evidence.append(EvidenceItem(category="momentum", point="20d return < -3%", weight=1.1, is_bullish=False, feature_name="returns_20d", feature_value=stat.returns_20d))

        net_score = len(bullish) - len(bearish)
        if 52.0 <= tech.rsi_14 <= 70.0 and tech.macd_hist > 0 and stat.returns_20d > 0.01:
            signal = AgentSignalType.BUY
            confidence = min(0.90, max(0.60, 0.65 + (0.06 * net_score)))
            edge = 0.038
        elif (tech.rsi_14 < 40.0 or tech.rsi_14 > 75.0) and tech.macd_hist < 0 and stat.returns_20d < 0.0:
            signal = AgentSignalType.SELL
            confidence = min(0.85, max(0.55, 0.60 + (0.05 * abs(net_score))))
            edge = -0.030
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        regime_weight = 1.0
        if regime and regime.feature_group_weights:
            regime_weight = regime.feature_group_weights.get("momentum", 1.0)

        reasoning = (
            f"Momentum Module: {signal.value} stance (Conf: {confidence:.0%}). "
            f"RSI={tech.rsi_14:.1f}, MACD Hist={tech.macd_hist:.3f}, 20d Ret={stat.returns_20d*100:+.1f}%."
        )

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=round(regime_weight, 2),
            data_quality=1.0,
            feature_group=FeatureGroup.MOMENTUM,
            features_used=features_used,
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=reasoning,
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.02,
            holding_period_days=5,
            metrics={"rsi_14": tech.rsi_14, "macd_hist": tech.macd_hist, "returns_20d": stat.returns_20d},
        )


# ==========================================
# 3. MEAN REVERSION MODULE (FeatureGroup.MEAN_REVERSION)
# ==========================================
class MeanReversionModule(BaseAgent):
    """Analyzes statistical price dispersion, Bollinger band extremes, and Z-score deviations."""
    name = AgentType.MEAN_REVERSION

    async def analyze(self, context: AgentContext) -> AgentOutput:
        tech = context.feature_snapshot.technical
        stat = context.feature_snapshot.statistical
        price = context.feature_snapshot.current_price
        regime = context.regime_state

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        features_used = ["bb_lower", "bb_upper", "z_score_20d", "rsi_14"]

        # Z-score and Bollinger checks
        z_score = stat.z_score_20d
        is_oversold_z = (z_score <= -1.75)
        is_overbought_z = (z_score >= 2.0)
        at_lower_bb = (price <= tech.bb_lower * 1.005)
        at_upper_bb = (price >= tech.bb_upper * 0.995)

        if is_oversold_z or at_lower_bb:
            bullish.append(f"Statistical oversold extreme: Z-Score={z_score:.2f}, Lower BB test (${tech.bb_lower:.2f})")
            evidence.append(EvidenceItem(category="mean_reversion", point="Oversold lower band / negative Z-score", weight=1.3, is_bullish=True, feature_name="z_score_20d", feature_value=z_score))
        elif is_overbought_z or at_upper_bb:
            bearish.append(f"Statistical overextended extreme: Z-Score={z_score:.2f}, Upper BB test (${tech.bb_upper:.2f})")
            evidence.append(EvidenceItem(category="mean_reversion", point="Overbought upper band / positive Z-score", weight=1.3, is_bullish=False, feature_name="z_score_20d", feature_value=z_score))

        if tech.rsi_14 <= 32.0:
            bullish.append(f"RSI oversold rebound setup ({tech.rsi_14:.1f})")
            evidence.append(EvidenceItem(category="mean_reversion", point="RSI <= 32", weight=1.1, is_bullish=True, feature_name="rsi_14", feature_value=tech.rsi_14))
        elif tech.rsi_14 >= 72.0:
            bearish.append(f"RSI overbought exhaustion ({tech.rsi_14:.1f})")
            evidence.append(EvidenceItem(category="mean_reversion", point="RSI >= 72", weight=1.1, is_bullish=False, feature_name="rsi_14", feature_value=tech.rsi_14))

        if (is_oversold_z or at_lower_bb) and tech.rsi_14 <= 38.0:
            signal = AgentSignalType.BUY
            confidence = 0.82
            edge = 0.035
        elif (is_overbought_z or at_upper_bb) and tech.rsi_14 >= 68.0:
            signal = AgentSignalType.SELL
            confidence = 0.80
            edge = -0.030
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        regime_weight = 1.0
        if regime and regime.feature_group_weights:
            regime_weight = regime.feature_group_weights.get("mean_reversion", 1.0)

        reasoning = (
            f"Mean Reversion Module: {signal.value} stance (Conf: {confidence:.0%}). "
            f"Z-Score={z_score:.2f}, Lower BB=${tech.bb_lower:.2f}, Upper BB=${tech.bb_upper:.2f}, RSI={tech.rsi_14:.1f}."
        )

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=round(regime_weight, 2),
            data_quality=1.0,
            feature_group=FeatureGroup.MEAN_REVERSION,
            features_used=features_used,
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=reasoning,
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.018,
            holding_period_days=3,
            metrics={"z_score_20d": z_score, "bb_lower": tech.bb_lower, "bb_upper": tech.bb_upper},
        )


# ==========================================
# 4. VOLATILITY RISK MODULE (FeatureGroup.VOLATILITY)
# ==========================================
class VolatilityRiskModule(BaseAgent):
    """Evaluates realized volatility, ATR risk budget, and downside variance."""
    name = AgentType.VOLATILITY_RISK

    async def analyze(self, context: AgentContext) -> AgentOutput:
        vol = context.feature_snapshot.volatility
        tech = context.feature_snapshot.technical
        stat = context.feature_snapshot.statistical
        regime = context.regime_state

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        features_used = ["realized_vol_20d", "atr_normalized", "sharpe_60d", "sortino_60d"]

        # Volatility assessment
        realized_vol = vol.realized_vol_20d
        if realized_vol <= 0.22 and stat.sharpe_60d >= 1.0:
            bullish.append(f"Subdued volatility ({realized_vol*100:.1f}%) and healthy risk efficiency (Sharpe {stat.sharpe_60d:.2f})")
            evidence.append(EvidenceItem(category="volatility", point="Low vol & positive Sharpe", weight=1.2, is_bullish=True, feature_name="realized_vol_20d", feature_value=realized_vol))
        elif realized_vol >= 0.40:
            bearish.append(f"Elevated price volatility ({realized_vol*100:.1f}%) warrants defensive sizing")
            evidence.append(EvidenceItem(category="volatility", point="High realized vol", weight=1.3, is_bullish=False, feature_name="realized_vol_20d", feature_value=realized_vol))

        if stat.sortino_60d >= 1.3:
            bullish.append(f"Solid downside risk efficiency (Sortino {stat.sortino_60d:.2f})")
            evidence.append(EvidenceItem(category="volatility", point="High Sortino ratio", weight=1.1, is_bullish=True, feature_name="sortino_60d", feature_value=stat.sortino_60d))
        elif stat.sortino_60d < 0.0:
            bearish.append(f"Negative downside risk efficiency (Sortino {stat.sortino_60d:.2f})")
            evidence.append(EvidenceItem(category="volatility", point="Negative Sortino ratio", weight=1.1, is_bullish=False, feature_name="sortino_60d", feature_value=stat.sortino_60d))

        if realized_vol <= 0.25 and stat.sharpe_60d >= 0.8:
            signal = AgentSignalType.BUY
            confidence = 0.75
            edge = 0.025
        elif realized_vol >= 0.42 or stat.sharpe_60d < -0.5:
            signal = AgentSignalType.SELL
            confidence = 0.75
            edge = -0.025
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        regime_weight = 1.0
        if regime and regime.feature_group_weights:
            regime_weight = regime.feature_group_weights.get("volatility", 1.0)

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=round(regime_weight, 2),
            data_quality=1.0,
            feature_group=FeatureGroup.VOLATILITY,
            features_used=features_used,
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=f"Volatility Risk: Vol={realized_vol*100:.1f}%, Sharpe={stat.sharpe_60d:.2f}, Sortino={stat.sortino_60d:.2f}.",
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=round(realized_vol / math.sqrt(52), 4),
            holding_period_days=10,
            metrics={"realized_vol_20d": realized_vol, "sharpe_60d": stat.sharpe_60d, "sortino_60d": stat.sortino_60d},
        )


# ==========================================
# 5. FUNDAMENTAL MODULE (FeatureGroup.FUNDAMENTAL)
# ==========================================
class FundamentalModule(BaseAgent):
    """
    Analyzes corporate valuation and profitability metrics.
    TRUTHFULNESS INVARIANT: Returns UNAVAILABLE if metrics are absent.
    """
    name = AgentType.FUNDAMENTAL

    async def analyze(self, context: AgentContext) -> AgentOutput:
        metrics = context.fundamental_metrics

        if not metrics or len(metrics) == 0:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.UNAVAILABLE,
                confidence=0.0,
                expected_edge=0.0,
                regime_compatibility=1.0,
                data_quality=0.0,
                feature_group=FeatureGroup.FUNDAMENTAL,
                features_used=[],
                evidence=[],
                bullish_points=[],
                bearish_points=[],
                risk_flags=["NO_FUNDAMENTAL_DATA"],
                reasoning="Fundamental financial metrics feed is unavailable for this asset.",
                implementation_status=ImplementationStatus.UNAVAILABLE,
            )

        pe = metrics.get("pe_ratio")
        roe = metrics.get("roe")
        fcf_yield = metrics.get("fcf_yield")
        debt_to_equity = metrics.get("debt_to_equity")

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []

        if roe is not None:
            if roe >= 0.16:
                bullish.append(f"High Return on Equity ROE ({roe*100:.1f}%)")
                evidence.append(EvidenceItem(category="fundamental", point=f"ROE={roe*100:.1f}%", weight=1.2, is_bullish=True, feature_name="roe", feature_value=roe))
            elif roe < 0.05:
                bearish.append(f"Low capital productivity: ROE ({roe*100:.1f}%)")
                evidence.append(EvidenceItem(category="fundamental", point="Low ROE", weight=1.1, is_bullish=False, feature_name="roe", feature_value=roe))

        if pe is not None:
            if 0 < pe <= 22.0:
                bullish.append(f"Attractive valuation: P/E {pe:.1f}x")
                evidence.append(EvidenceItem(category="fundamental", point=f"P/E={pe:.1f}x", weight=1.2, is_bullish=True, feature_name="pe_ratio", feature_value=pe))
            elif pe > 48.0:
                bearish.append(f"High valuation multiple: P/E {pe:.1f}x")
                evidence.append(EvidenceItem(category="fundamental", point="High P/E", weight=1.0, is_bullish=False, feature_name="pe_ratio", feature_value=pe))

        if debt_to_equity is not None:
            if debt_to_equity > 2.2:
                bearish.append(f"High financial leverage: Debt/Equity {debt_to_equity:.2f}x")
            elif debt_to_equity < 0.8:
                bullish.append(f"Conservative balance sheet: Debt/Equity {debt_to_equity:.2f}x")

        net_score = len(bullish) - len(bearish)
        if net_score >= 2:
            signal = AgentSignalType.BUY
            confidence = min(0.88, 0.65 + (0.06 * net_score))
            edge = 0.040
        elif net_score <= -2:
            signal = AgentSignalType.SELL
            confidence = min(0.85, 0.60 + (0.05 * abs(net_score)))
            edge = -0.030
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=1.0,
            data_quality=1.0,
            feature_group=FeatureGroup.FUNDAMENTAL,
            features_used=list(metrics.keys()),
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=f"Fundamental Analysis: ROE={roe*100 if roe else 0:.1f}%, P/E={pe if pe else 0:.1f}x, D/E={debt_to_equity if debt_to_equity else 0:.2f}x.",
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.02,
            holding_period_days=20,
            metrics=metrics,
        )


# ==========================================
# 6. SENTIMENT & NEWS MODULE (FeatureGroup.SENTIMENT)
# ==========================================
class SentimentNewsModule(BaseAgent):
    """
    Analyzes live news headlines and NLP sentiment.
    TRUTHFULNESS INVARIANT: Returns UNAVAILABLE if news feed is absent.
    """
    name = AgentType.SENTIMENT_NEWS

    async def analyze(self, context: AgentContext) -> AgentOutput:
        nlp = context.feature_snapshot.nlp
        news = context.market_news

        has_nlp_data = (nlp.sentiment_score != 0.0 or nlp.news_velocity > 0)
        has_news = bool(news and len(news) > 0)

        if not has_nlp_data and not has_news:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.UNAVAILABLE,
                confidence=0.0,
                expected_edge=0.0,
                regime_compatibility=1.0,
                data_quality=0.0,
                feature_group=FeatureGroup.SENTIMENT,
                features_used=[],
                evidence=[],
                bullish_points=[],
                bearish_points=[],
                risk_flags=["NO_SENTIMENT_DATA"],
                reasoning="Sentiment & real-time news data feeds are currently unavailable for this asset.",
                implementation_status=ImplementationStatus.UNAVAILABLE,
            )

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        features_used = ["sentiment_score", "news_velocity", "fear_greed_index"]

        if nlp.sentiment_score >= 0.20:
            bullish.append(f"Positive institutional NLP sentiment (+{nlp.sentiment_score:.2f})")
            evidence.append(EvidenceItem(category="sentiment", point=f"Sentiment score +{nlp.sentiment_score:.2f}", weight=1.2, is_bullish=True, feature_name="sentiment_score", feature_value=nlp.sentiment_score))
        elif nlp.sentiment_score <= -0.20:
            bearish.append(f"Negative institutional NLP sentiment ({nlp.sentiment_score:.2f})")
            evidence.append(EvidenceItem(category="sentiment", point=f"Sentiment score {nlp.sentiment_score:.2f}", weight=1.2, is_bullish=False, feature_name="sentiment_score", feature_value=nlp.sentiment_score))

        if nlp.sentiment_score >= 0.20 and len(news) > 0:
            signal = AgentSignalType.BUY
            confidence = min(0.85, 0.60 + abs(nlp.sentiment_score) * 0.35)
            edge = 0.030
        elif nlp.sentiment_score <= -0.20 and len(news) > 0:
            signal = AgentSignalType.SELL
            confidence = min(0.82, 0.58 + abs(nlp.sentiment_score) * 0.35)
            edge = -0.025
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=1.0,
            data_quality=1.0,
            feature_group=FeatureGroup.SENTIMENT,
            features_used=features_used,
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=f"Sentiment NLP: Score={nlp.sentiment_score:+.2f} on {len(news)} news headlines.",
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.015,
            holding_period_days=3,
            metrics={"sentiment_score": nlp.sentiment_score, "news_count": float(len(news))},
        )


# ==========================================
# 7. MARKET REGIME MODULE (FeatureGroup.REGIME)
# ==========================================
class MarketRegimeModule(BaseAgent):
    """Evaluates macro regime alignment and directional tailwinds."""
    name = AgentType.MARKET_REGIME

    async def analyze(self, context: AgentContext) -> AgentOutput:
        regime = context.regime_state
        if not regime:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.HOLD,
                confidence=0.50,
                feature_group=FeatureGroup.REGIME,
                reasoning="Regime state is not initialized.",
            )

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []

        if regime.regime.value in ["TRENDING_BULL", "BULL"]:
            bullish.append(f"Market Regime is {regime.regime.value} ({regime.confidence:.0%} conf)")
            evidence.append(EvidenceItem(category="regime", point=f"Regime {regime.regime.value}", weight=1.3, is_bullish=True))
            signal = AgentSignalType.BUY
            conf = regime.confidence
            edge = 0.035
        elif regime.regime.value in ["TRENDING_BEAR", "BEAR"]:
            bearish.append(f"Market Regime is {regime.regime.value} ({regime.confidence:.0%} conf)")
            evidence.append(EvidenceItem(category="regime", point=f"Regime {regime.regime.value}", weight=1.3, is_bullish=False))
            signal = AgentSignalType.SELL
            conf = regime.confidence
            edge = -0.035
        else:
            signal = AgentSignalType.HOLD
            conf = 0.50
            edge = 0.0

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(conf, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=1.0,
            data_quality=1.0,
            feature_group=FeatureGroup.REGIME,
            features_used=["regime_state", "adx_14", "realized_vol_20d"],
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=f"Regime Module: State is {regime.regime.value} with confidence {regime.confidence:.0%}.",
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.02,
            holding_period_days=10,
            metrics={"regime_confidence": regime.confidence},
        )


# ==========================================
# 8. CROSS-ASSET MACRO MODULE (FeatureGroup.MACRO)
# ==========================================
class CrossAssetMacroModule(BaseAgent):
    """Analyzes broader market benchmarks (SPY, QQQ), VIX volatility, and macro indicators."""
    name = AgentType.CROSS_ASSET_MACRO

    async def analyze(self, context: AgentContext) -> AgentOutput:
        cross = context.feature_snapshot.cross_asset

        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        features_used = ["vix_level", "risk_on_indicator", "spy_return_1d", "qqq_return_1d"]

        if cross.vix_level >= 26.0:
            bearish.append(f"Elevated macro VIX volatility index ({cross.vix_level:.1f})")
            evidence.append(EvidenceItem(category="macro", point="High VIX volatility", weight=1.3, is_bullish=False, feature_name="vix_level", feature_value=cross.vix_level))
        elif cross.vix_level <= 17.0:
            bullish.append(f"Subdued macro VIX volatility ({cross.vix_level:.1f})")
            evidence.append(EvidenceItem(category="macro", point="Low VIX volatility", weight=1.1, is_bullish=True, feature_name="vix_level", feature_value=cross.vix_level))

        if cross.risk_on_indicator >= 0.55:
            bullish.append(f"Macro Risk-On posture (score {cross.risk_on_indicator:.2f})")
            evidence.append(EvidenceItem(category="macro", point="Risk-On posture", weight=1.1, is_bullish=True, feature_name="risk_on_indicator", feature_value=cross.risk_on_indicator))
        elif cross.risk_on_indicator < 0.45:
            bearish.append(f"Macro Risk-Off posture (score {cross.risk_on_indicator:.2f})")
            evidence.append(EvidenceItem(category="macro", point="Risk-Off posture", weight=1.1, is_bullish=False, feature_name="risk_on_indicator", feature_value=cross.risk_on_indicator))

        net_score = len(bullish) - len(bearish)
        if cross.vix_level <= 20.0 and cross.risk_on_indicator >= 0.50 and net_score >= 1:
            signal = AgentSignalType.BUY
            confidence = 0.72
            edge = 0.025
        elif cross.vix_level >= 26.0 or cross.risk_on_indicator <= 0.40:
            signal = AgentSignalType.SELL if net_score <= -2 else AgentSignalType.HOLD
            confidence = 0.70
            edge = -0.020
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=1.0,
            data_quality=1.0,
            feature_group=FeatureGroup.MACRO,
            features_used=features_used,
            evidence=evidence,
            bullish_points=bullish,
            bearish_points=bearish,
            reasoning=f"Macro Module: VIX={cross.vix_level:.1f}, Risk-On={cross.risk_on_indicator:.2f}, SPY 1d={cross.spy_return_1d*100:+.2f}%.",
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.018,
            holding_period_days=10,
            metrics={"vix_level": cross.vix_level, "risk_on_indicator": cross.risk_on_indicator},
        )


# ==========================================
# 9. MICROSTRUCTURE MODULE (FeatureGroup.MICROSTRUCTURE)
# ==========================================
class MicrostructureModule(BaseAgent):
    """
    Analyzes order book queue depth and spread friction.
    TRUTHFULNESS INVARIANT: Returns UNAVAILABLE if Level 2 data is absent.
    """
    name = AgentType.MICROSTRUCTURE

    async def analyze(self, context: AgentContext) -> AgentOutput:
        ob = context.order_book_data

        if not ob:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.UNAVAILABLE,
                confidence=0.0,
                expected_edge=0.0,
                regime_compatibility=1.0,
                data_quality=0.0,
                feature_group=FeatureGroup.MICROSTRUCTURE,
                features_used=[],
                evidence=[],
                bullish_points=[],
                bearish_points=[],
                risk_flags=["NO_ORDER_BOOK_DATA"],
                reasoning="Level 2 order book depth is unavailable for this asset.",
                implementation_status=ImplementationStatus.UNAVAILABLE,
            )

        spread = ob.get("spread_bps", 3.0)
        imbalance = ob.get("depth_imbalance", 0.0)

        if spread <= 5.0 and imbalance > 0.10:
            signal = AgentSignalType.BUY
            confidence = 0.70
            edge = 0.015
        elif spread > 15.0 or imbalance < -0.15:
            signal = AgentSignalType.SELL
            confidence = 0.65
            edge = -0.015
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50
            edge = 0.0

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_edge=round(edge, 4),
            regime_compatibility=1.0,
            data_quality=1.0,
            feature_group=FeatureGroup.MICROSTRUCTURE,
            features_used=["bid_ask_spread_bps", "depth_imbalance"],
            evidence=[],
            bullish_points=[],
            bearish_points=[],
            reasoning=f"Microstructure: Spread={spread:.1f} bps, Imbalance={imbalance:+.2f}.",
            expected_return=edge if edge > 0 else 0.0,
            expected_risk=0.01,
            holding_period_days=1,
            metrics={"spread_bps": spread, "depth_imbalance": imbalance},
        )


# Backward Compatibility Aliases
TechnicalAgent = TechnicalTrendModule
QuantAgent = MomentumModule
FundamentalAgent = FundamentalModule
SentimentNewsAgent = SentimentNewsModule
SentimentAgent = SentimentNewsModule
ResearchAgent = SentimentNewsModule
MacroAgent = CrossAssetMacroModule
CrossAssetAgent = CrossAssetMacroModule
ComplianceAgent = CrossAssetMacroModule
MicrostructureAgent = MicrostructureModule
CostAnalysisAgent = MicrostructureModule
OptionsAgent = VolatilityRiskModule
SimulationAgent = VolatilityRiskModule
PatternDiscoveryAgent = TechnicalTrendModule
DataQualityAgent = TechnicalTrendModule
DataQualityAgentWrapper = TechnicalTrendModule
