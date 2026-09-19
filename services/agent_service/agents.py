"""
ATHENA V2 Directional Research Agents
Implements the 6 Core Directional Research Agents with strict truthfulness invariants:
1. TechnicalAgent (Price action, momentum, trend, pattern analysis)
2. QuantAgent (Statistical returns, Z-score, risk-adjusted ratios, VaR simulation)
3. FundamentalAgent (Financial statement & valuation metrics; UNAVAILABLE if not present)
4. SentimentNewsAgent (News & NLP sentiment; UNAVAILABLE if feed is empty)
5. MacroAgent (Intermarket, regime state, yields, VIX, risk-on indicator)
6. MicrostructureAgent (Order book depth, bid-ask spreads; UNAVAILABLE if feed is empty)
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
    ImplementationStatus,
)
from .base import BaseAgent
from .analyzers.pattern_analyzer import PatternAnalyzer
from .analyzers.cross_asset_analyzer import CrossAssetAnalyzer
from .analyzers.risk_simulation import RiskSimulationAnalyzer


# ==========================================
# 1. TECHNICAL AGENT
# ==========================================
class TechnicalAgent(BaseAgent):
    """
    Analyzes price action, trend alignment, momentum, and chart structure.
    Uses PatternAnalyzer for support/resistance and consolidation detection.
    """
    name = AgentType.TECHNICAL

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.pattern_analyzer = PatternAnalyzer()

    async def analyze(self, context: AgentContext) -> AgentOutput:
        tech = context.feature_snapshot.technical
        price = context.feature_snapshot.current_price

        bullish = []
        bearish = []
        evidence = []
        risk_flags = []
        features_used = ["ema_9", "ema_21", "ema_50", "ema_200", "rsi_14", "macd_hist", "atr_14", "pivot_structure"]

        # EMA Trend alignment
        if tech.ema_9 > tech.ema_21 > tech.ema_50:
            bullish.append("Bullish moving average stack: EMA 9 > EMA 21 > EMA 50")
            evidence.append(EvidenceItem(category="technical", point="EMA 9 > 21 > 50 stack", weight=1.3, is_bullish=True))
        elif tech.ema_9 > tech.ema_21:
            bullish.append("Short-term EMA 9 > EMA 21 bullish crossover")
            evidence.append(EvidenceItem(category="technical", point="EMA 9 > 21", weight=1.1, is_bullish=True))
        elif tech.ema_9 < tech.ema_21 < tech.ema_50:
            bearish.append("Bearish moving average stack: EMA 9 < EMA 21 < EMA 50")
            evidence.append(EvidenceItem(category="technical", point="EMA 9 < 21 < 50 stack", weight=1.3, is_bullish=False))
        else:
            bearish.append("EMA 9 < EMA 21 bearish divergence")
            evidence.append(EvidenceItem(category="technical", point="EMA 9 < 21", weight=1.0, is_bullish=False))

        # Long term 200 EMA trend filter
        if tech.ema_200 > 0:
            if price > tech.ema_200:
                bullish.append(f"Price (${price:.2f}) above 200-day EMA (${tech.ema_200:.2f})")
                evidence.append(EvidenceItem(category="technical", point="Price above EMA 200", weight=1.2, is_bullish=True))
            else:
                bearish.append(f"Price (${price:.2f}) below 200-day EMA (${tech.ema_200:.2f})")
                evidence.append(EvidenceItem(category="technical", point="Price below EMA 200", weight=1.2, is_bullish=False))

        # Momentum: RSI 14
        if 50 < tech.rsi_14 < 70:
            bullish.append(f"RSI ({tech.rsi_14:.1f}) in healthy expansion zone (50-70)")
            evidence.append(EvidenceItem(category="technical", point=f"RSI={tech.rsi_14:.1f}", weight=1.0, is_bullish=True))
        elif tech.rsi_14 >= 70:
            bearish.append(f"RSI ({tech.rsi_14:.1f}) in overbought exhaustion territory")
            risk_flags.append(f"RSI overbought ({tech.rsi_14:.1f})")
            evidence.append(EvidenceItem(category="technical", point="RSI overbought", weight=0.9, is_bullish=False))
        elif tech.rsi_14 <= 30:
            bullish.append(f"RSI ({tech.rsi_14:.1f}) oversold potential reversal")
            evidence.append(EvidenceItem(category="technical", point="RSI oversold", weight=1.0, is_bullish=True))

        # Momentum: MACD Histogram
        if tech.macd_hist > 0:
            bullish.append(f"MACD histogram positive (+{tech.macd_hist:.3f})")
            evidence.append(EvidenceItem(category="technical", point="Positive MACD hist", weight=1.0, is_bullish=True))
        else:
            bearish.append(f"MACD histogram negative ({tech.macd_hist:.3f})")
            evidence.append(EvidenceItem(category="technical", point="Negative MACD hist", weight=1.0, is_bullish=False))

        # Pattern Analyzer integration
        pattern_res = self.pattern_analyzer.analyze_pattern(context.feature_snapshot)
        if pattern_res.get("is_breakout_candidate"):
            bullish.append(f"Pattern: Breakout candidate above pivot resistance (${tech.pivot_resistance:.2f})")
            evidence.append(EvidenceItem(category="technical", point="Resistance breakout structure", weight=1.2, is_bullish=True))
        elif pattern_res.get("is_pullback_candidate"):
            bullish.append(f"Pattern: Pullback test of EMA 21 support (${tech.ema_21:.2f})")
            evidence.append(EvidenceItem(category="technical", point="EMA 21 support pullback", weight=1.1, is_bullish=True))

        # Signal determination
        net_score = len(bullish) - len(bearish)
        if net_score >= 2:
            signal = AgentSignalType.BUY
            confidence = min(0.92, max(0.60, 0.60 + 0.06 * net_score))
        elif net_score <= -2:
            signal = AgentSignalType.SELL
            confidence = min(0.90, max(0.55, 0.55 + 0.06 * abs(net_score)))
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50

        atr_pct = round(tech.atr_14 / price, 4) if price > 0 else 0.02
        reasoning = (
            f"Technical analysis indicates {signal.value} stance (Confidence {confidence:.0%}). "
            f"Price ${price:.2f} relative to EMA 21 (${tech.ema_21:.2f}) & EMA 200 (${tech.ema_200:.2f}). "
            f"Pivot Support: ${tech.pivot_support:.2f}, Pivot Resistance: ${tech.pivot_resistance:.2f}."
        )

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_return=0.045 if signal == AgentSignalType.BUY else (-0.035 if signal == AgentSignalType.SELL else 0.0),
            expected_risk=atr_pct,
            holding_period_days=5,
            reasoning=reasoning,
            bullish_points=bullish,
            bearish_points=bearish,
            evidence=evidence,
            risk_flags=risk_flags,
            features_used=features_used,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            metrics={"rsi_14": tech.rsi_14, "macd_hist": tech.macd_hist, "adx_14": tech.adx_14, "atr_14": tech.atr_14},
        )


# ==========================================
# 2. QUANT AGENT
# ==========================================
class QuantAgent(BaseAgent):
    """
    Analyzes statistical distribution, Z-scores, factor alphas, Sharpe/Sortino ratios,
    and empirical Value-at-Risk simulations.
    """
    name = AgentType.QUANT

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.risk_sim = RiskSimulationAnalyzer()

    async def analyze(self, context: AgentContext) -> AgentOutput:
        stat = context.feature_snapshot.statistical
        vol = context.feature_snapshot.volatility
        price = context.feature_snapshot.current_price

        bullish = []
        bearish = []
        evidence = []
        risk_flags = []
        features_used = ["sharpe_60d", "sortino_60d", "z_score_20d", "alpha_annual", "beta_spy", "realized_vol_20d"]

        # 1. Sharpe & Sortino evaluation
        if stat.sharpe_60d >= 1.2:
            bullish.append(f"High risk-adjusted efficiency (60d Sharpe {stat.sharpe_60d:.2f})")
            evidence.append(EvidenceItem(category="quant", point="High Sharpe ratio", weight=1.3, is_bullish=True))
        elif stat.sharpe_60d < 0.0:
            bearish.append(f"Negative risk-adjusted return (Sharpe {stat.sharpe_60d:.2f})")
            evidence.append(EvidenceItem(category="quant", point="Negative Sharpe", weight=1.2, is_bullish=False))

        if stat.sortino_60d >= 1.5:
            bullish.append(f"Strong downside protection (Sortino {stat.sortino_60d:.2f})")
            evidence.append(EvidenceItem(category="quant", point="High Sortino ratio", weight=1.1, is_bullish=True))

        # 2. Statistical Mean Reversion Z-Score
        if stat.z_score_20d <= -1.8:
            bullish.append(f"Statistical oversold dip: 20-day price Z-Score is {stat.z_score_20d:.2f} standard deviations")
            evidence.append(EvidenceItem(category="quant", point="Oversold Z-score", weight=1.2, is_bullish=True))
        elif stat.z_score_20d >= 2.2:
            bearish.append(f"Statistical overbought extension: Z-Score is +{stat.z_score_20d:.2f} standard deviations")
            risk_flags.append(f"High Z-Score ({stat.z_score_20d:.2f})")
            evidence.append(EvidenceItem(category="quant", point="Overextended Z-score", weight=1.1, is_bullish=False))

        # 3. Alpha & Realized Volatility
        if stat.alpha_annual > 0.05:
            bullish.append(f"Positive annual factor alpha (+{stat.alpha_annual*100:.1f}%)")
            evidence.append(EvidenceItem(category="quant", point="Positive factor alpha", weight=1.1, is_bullish=True))

        if vol.realized_vol_20d > 0.45:
            risk_flags.append(f"Elevated 20-day realized volatility ({vol.realized_vol_20d*100:.1f}%)")
            bearish.append(f"High realized volatility ({vol.realized_vol_20d*100:.1f}%) increases downside variance")

        # 4. Optional Risk Simulation (VaR)
        returns = context.extra_context.get("returns_series", [])
        if returns and len(returns) >= 20:
            features_used.append("risk_simulation")
            sim_res = self.risk_sim.analyze(returns, current_price=price)
            if sim_res.get("is_available"):
                var_95 = sim_res.get("var_95_pct", 0.0)
                if var_95 < 0.03:
                    bullish.append(f"Favorable 1-day 95% Historical VaR ({var_95*100:.1f}%)")
                elif var_95 > 0.06:
                    risk_flags.append(f"Elevated 1-day VaR 95% ({var_95*100:.1f}%)")

        net_score = len(bullish) - len(bearish)
        if net_score >= 2:
            signal = AgentSignalType.BUY
            confidence = min(0.90, max(0.60, 0.62 + 0.06 * net_score))
        elif net_score <= -2:
            signal = AgentSignalType.SELL
            confidence = min(0.88, max(0.55, 0.58 + 0.06 * abs(net_score)))
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50

        expected_ret = round(stat.alpha_annual / 12.0 + 0.015, 4) if signal == AgentSignalType.BUY else 0.0
        expected_rk = round(vol.realized_vol_20d / math.sqrt(52), 4)

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_return=expected_ret,
            expected_risk=expected_rk,
            holding_period_days=10,
            reasoning=f"Quant statistical analysis: Sharpe={stat.sharpe_60d:.2f}, Sortino={stat.sortino_60d:.2f}, Z-Score={stat.z_score_20d:.2f}, Alpha={stat.alpha_annual*100:.1f}%.",
            bullish_points=bullish,
            bearish_points=bearish,
            evidence=evidence,
            risk_flags=risk_flags,
            features_used=features_used,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            metrics={"sharpe_60d": stat.sharpe_60d, "sortino_60d": stat.sortino_60d, "z_score_20d": stat.z_score_20d, "beta_spy": stat.beta_spy, "alpha_annual": stat.alpha_annual},
        )


# ==========================================
# 3. FUNDAMENTAL AGENT
# ==========================================
class FundamentalAgent(BaseAgent):
    """
    Analyzes corporate financial statements, valuation multiples (PE, PB, EV/EBITDA),
    profitability (ROE, ROIC), and debt solvency.
    TRUTHFULNESS INVARIANT: Returns UNAVAILABLE if fundamental metrics are not provided.
    """
    name = AgentType.FUNDAMENTAL

    async def analyze(self, context: AgentContext) -> AgentOutput:
        metrics = context.fundamental_metrics

        # Truthfulness gate: if no fundamental metrics are provided, explicitly return UNAVAILABLE
        if not metrics or len(metrics) == 0:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.UNAVAILABLE,
                confidence=0.0,
                expected_return=0.0,
                expected_risk=0.0,
                holding_period_days=0,
                reasoning="Fundamental research feed is unavailable for this asset (no genuine financial statement data provided).",
                bullish_points=[],
                bearish_points=[],
                evidence=[],
                risk_flags=["NO_FUNDAMENTAL_DATA"],
                features_used=[],
                implementation_status=ImplementationStatus.UNAVAILABLE,
                metrics={},
            )

        pe = metrics.get("pe_ratio")
        roe = metrics.get("roe")
        fcf_yield = metrics.get("fcf_yield")
        debt_to_equity = metrics.get("debt_to_equity")

        bullish = []
        bearish = []
        evidence = []
        risk_flags = []
        features_used = list(metrics.keys())

        if roe is not None:
            if roe >= 0.18:
                bullish.append(f"High Return on Equity ROE ({roe*100:.1f}%)")
                evidence.append(EvidenceItem(category="fundamental", point=f"ROE={roe*100:.1f}%", weight=1.3, is_bullish=True))
            elif roe < 0.05:
                bearish.append(f"Subdued capital productivity: ROE ({roe*100:.1f}%)")
                evidence.append(EvidenceItem(category="fundamental", point="Low ROE", weight=1.1, is_bullish=False))

        if pe is not None:
            if 0 < pe <= 20.0:
                bullish.append(f"Attractive valuation multiple: P/E {pe:.1f}x")
                evidence.append(EvidenceItem(category="fundamental", point=f"P/E={pe:.1f}x", weight=1.2, is_bullish=True))
            elif pe > 45.0:
                bearish.append(f"High valuation premium: P/E {pe:.1f}x")
                risk_flags.append(f"High P/E multiple ({pe:.1f}x)")
                evidence.append(EvidenceItem(category="fundamental", point="High P/E", weight=1.0, is_bullish=False))

        if debt_to_equity is not None:
            if debt_to_equity > 2.0:
                bearish.append(f"High financial leverage: Debt/Equity {debt_to_equity:.2f}x")
                risk_flags.append("High debt leverage")
            elif debt_to_equity < 0.8:
                bullish.append(f"Conservative balance sheet: Debt/Equity {debt_to_equity:.2f}x")

        if fcf_yield is not None and fcf_yield > 0.04:
            bullish.append(f"Strong Free Cash Flow Yield ({fcf_yield*100:.1f}%)")
            evidence.append(EvidenceItem(category="fundamental", point="Strong FCF Yield", weight=1.1, is_bullish=True))

        net_score = len(bullish) - len(bearish)
        if net_score >= 2:
            signal = AgentSignalType.BUY
            confidence = min(0.88, max(0.60, 0.65 + 0.06 * net_score))
        elif net_score <= -2:
            signal = AgentSignalType.SELL
            confidence = min(0.85, max(0.55, 0.60 + 0.06 * abs(net_score)))
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_return=0.05 if signal == AgentSignalType.BUY else 0.0,
            expected_risk=0.025,
            holding_period_days=20,
            reasoning=f"Fundamental evaluation: ROE={roe*100 if roe else 0:.1f}%, P/E={pe if pe else 0:.1f}x, D/E={debt_to_equity if debt_to_equity else 0:.2f}x.",
            bullish_points=bullish,
            bearish_points=bearish,
            evidence=evidence,
            risk_flags=risk_flags,
            features_used=features_used,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            metrics=metrics,
        )


# ==========================================
# 4. SENTIMENT & NEWS AGENT
# ==========================================
class SentimentNewsAgent(BaseAgent):
    """
    Analyzes real textual news feed sentiment and quantitative NLP signals.
    TRUTHFULNESS INVARIANT: Returns UNAVAILABLE if both news feeds and NLP scores are absent.
    """
    name = AgentType.SENTIMENT_NEWS

    async def analyze(self, context: AgentContext) -> AgentOutput:
        nlp = context.feature_snapshot.nlp
        news = context.market_news

        has_nlp_data = (nlp.sentiment_score != 0.0 or nlp.bullish_percentage != 0.5)
        has_news = bool(news and len(news) > 0)

        # Truthfulness check: if no genuine news and no NLP model output, return UNAVAILABLE
        if not has_nlp_data and not has_news:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.UNAVAILABLE,
                confidence=0.0,
                expected_return=0.0,
                expected_risk=0.0,
                holding_period_days=0,
                reasoning="Sentiment and real-time news data feeds are currently unavailable for this asset.",
                bullish_points=[],
                bearish_points=[],
                evidence=[],
                risk_flags=["NO_SENTIMENT_DATA"],
                features_used=[],
                implementation_status=ImplementationStatus.UNAVAILABLE,
                metrics={},
            )

        bullish = []
        bearish = []
        evidence = []
        risk_flags = []
        features_used = ["nlp_sentiment_score", "fear_greed_index"]

        if nlp.sentiment_score > 0.20:
            bullish.append(f"Positive institutional NLP sentiment score (+{nlp.sentiment_score:.2f})")
            evidence.append(EvidenceItem(category="sentiment", point=f"Sentiment score +{nlp.sentiment_score:.2f}", weight=1.2, is_bullish=True))
        elif nlp.sentiment_score < -0.20:
            bearish.append(f"Negative NLP sentiment score ({nlp.sentiment_score:.2f})")
            evidence.append(EvidenceItem(category="sentiment", point=f"Sentiment score {nlp.sentiment_score:.2f}", weight=1.2, is_bullish=False))

        if nlp.fear_greed_index > 75:
            risk_flags.append(f"Extreme market greed ({nlp.fear_greed_index:.0f}/100)")
            bearish.append("Broad market sentiment in Extreme Greed territory")
        elif nlp.fear_greed_index < 25:
            bullish.append(f"Contrarian extreme fear reading ({nlp.fear_greed_index:.0f}/100)")
            evidence.append(EvidenceItem(category="sentiment", point="Contrarian fear index", weight=1.1, is_bullish=True))

        if has_news:
            features_used.append("market_news_stream")
            bullish.append(f"Processed {len(news)} live market news headlines")

        net_score = len(bullish) - len(bearish)
        if net_score >= 1 and nlp.sentiment_score >= 0.10:
            signal = AgentSignalType.BUY
            confidence = min(0.88, max(0.60, 0.60 + abs(nlp.sentiment_score) * 0.4))
        elif net_score <= -1 and nlp.sentiment_score <= -0.10:
            signal = AgentSignalType.SELL
            confidence = min(0.85, max(0.55, 0.55 + abs(nlp.sentiment_score) * 0.4))
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_return=0.035 if signal == AgentSignalType.BUY else 0.0,
            expected_risk=0.02,
            holding_period_days=3,
            reasoning=f"NLP Sentiment score +{nlp.sentiment_score:.2f} ({nlp.bullish_percentage*100:.0f}% bullish). Fear/Greed at {nlp.fear_greed_index:.0f}.",
            bullish_points=bullish,
            bearish_points=bearish,
            evidence=evidence,
            risk_flags=risk_flags,
            features_used=features_used,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            metrics={"sentiment_score": nlp.sentiment_score, "fear_greed_index": nlp.fear_greed_index, "news_count": len(news)},
        )


# ==========================================
# 5. MACRO AGENT
# ==========================================
class MacroAgent(BaseAgent):
    """
    Analyzes macroeconomic conditions, broad market indices (SPY, QQQ, VIX),
    sovereign bond yields, and cross-asset risk-on appetite.
    """
    name = AgentType.MACRO

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.cross_asset = CrossAssetAnalyzer()

    async def analyze(self, context: AgentContext) -> AgentOutput:
        cross = context.feature_snapshot.cross_asset
        regime = context.regime_state
        macro_dict = context.macro_indicators

        bullish = []
        bearish = []
        evidence = []
        risk_flags = []
        features_used = ["risk_on_indicator", "vix_level", "spy_return_1d", "qqq_return_1d"]

        # 1. Risk-On / Risk-Off indicator
        if cross.risk_on_indicator >= 0.55:
            bullish.append(f"Global macro is Risk-On (appetite score {cross.risk_on_indicator:.2f})")
            evidence.append(EvidenceItem(category="macro", point="Risk-on environment", weight=1.3, is_bullish=True))
        elif cross.risk_on_indicator < 0.45:
            bearish.append(f"Global macro is Risk-Off (appetite score {cross.risk_on_indicator:.2f})")
            evidence.append(EvidenceItem(category="macro", point="Risk-off environment", weight=1.3, is_bullish=False))

        # 2. VIX Volatility Index
        if cross.vix_level > 25.0:
            bearish.append(f"Elevated broad market VIX ({cross.vix_level:.1f})")
            risk_flags.append(f"High VIX ({cross.vix_level:.1f})")
            evidence.append(EvidenceItem(category="macro", point="High VIX volatility", weight=1.2, is_bullish=False))
        elif cross.vix_level < 18.0:
            bullish.append(f"Subdued equity volatility (VIX {cross.vix_level:.1f})")
            evidence.append(EvidenceItem(category="macro", point="Low VIX volatility", weight=1.1, is_bullish=True))

        # 3. Market Regime integration
        if regime:
            features_used.append("regime_state")
            if regime.regime.value in ["BULL", "BULL_TREND"]:
                bullish.append(f"Market Regime is {regime.regime.value} (Confidence {regime.confidence:.0%})")
                evidence.append(EvidenceItem(category="macro", point=f"Regime {regime.regime.value}", weight=1.2, is_bullish=True))
            elif regime.regime.value in ["BEAR", "BEAR_TREND"]:
                bearish.append(f"Market Regime is {regime.regime.value} (Confidence {regime.confidence:.0%})")
                evidence.append(EvidenceItem(category="macro", point=f"Regime {regime.regime.value}", weight=1.2, is_bullish=False))

        net_score = len(bullish) - len(bearish)
        if net_score >= 1 and cross.risk_on_indicator >= 0.50:
            signal = AgentSignalType.BUY
            confidence = min(0.88, max(0.60, 0.65 + 0.05 * net_score))
        elif net_score <= -1:
            signal = AgentSignalType.SELL if net_score <= -2 else AgentSignalType.HOLD
            confidence = min(0.82, max(0.55, 0.58 + 0.05 * abs(net_score)))
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_return=0.03 if signal == AgentSignalType.BUY else 0.0,
            expected_risk=0.018,
            holding_period_days=15,
            reasoning=f"Macro environment: Risk-on score {cross.risk_on_indicator:.2f}, VIX={cross.vix_level:.1f}, SPY 1d={cross.spy_return_1d*100:.2f}%.",
            bullish_points=bullish,
            bearish_points=bearish,
            evidence=evidence,
            risk_flags=risk_flags,
            features_used=features_used,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            metrics={"risk_on_indicator": cross.risk_on_indicator, "vix_level": cross.vix_level, "spy_return": cross.spy_return_1d},
        )


# ==========================================
# 6. MICROSTRUCTURE AGENT
# ==========================================
class MicrostructureAgent(BaseAgent):
    """
    Analyzes order book queue depth, bid-ask spread friction, and order flow imbalance.
    TRUTHFULNESS INVARIANT: Returns UNAVAILABLE if order book or liquidity metrics are absent.
    """
    name = AgentType.MICROSTRUCTURE

    async def analyze(self, context: AgentContext) -> AgentOutput:
        liq = context.feature_snapshot.liquidity
        ob = context.order_book_data

        has_liquidity = (liq.bid_ask_spread_bps > 0.0 or liq.depth_imbalance != 0.0 or ob is not None)

        # Truthfulness check: if no genuine liquidity or order book depth, return UNAVAILABLE
        if not has_liquidity:
            return AgentOutput(
                agent=self.name,
                symbol=context.symbol,
                signal=AgentSignalType.UNAVAILABLE,
                confidence=0.0,
                expected_return=0.0,
                expected_risk=0.0,
                holding_period_days=0,
                reasoning="Order book depth and Level 2 microstructure data feed is currently unavailable.",
                bullish_points=[],
                bearish_points=[],
                evidence=[],
                risk_flags=["NO_MICROSTRUCTURE_DATA"],
                features_used=[],
                implementation_status=ImplementationStatus.UNAVAILABLE,
                metrics={},
            )

        bullish = []
        bearish = []
        evidence = []
        risk_flags = []
        features_used = ["bid_ask_spread_bps", "depth_imbalance", "turnover_ratio"]

        # Bid-ask spread evaluation
        if liq.bid_ask_spread_bps <= 3.0:
            bullish.append(f"Tight institutional bid-ask spread ({liq.bid_ask_spread_bps:.1f} bps)")
            evidence.append(EvidenceItem(category="microstructure", point="Tight spread < 3bps", weight=1.2, is_bullish=True))
        elif liq.bid_ask_spread_bps > 15.0:
            bearish.append(f"Wide bid-ask spread friction ({liq.bid_ask_spread_bps:.1f} bps)")
            risk_flags.append(f"High spread friction ({liq.bid_ask_spread_bps:.1f} bps)")
            evidence.append(EvidenceItem(category="microstructure", point="Wide spread > 15bps", weight=1.1, is_bullish=False))

        # Order book depth imbalance
        if liq.depth_imbalance > 0.08:
            bullish.append(f"Positive order book depth imbalance (+{liq.depth_imbalance*100:.1f}% bid side)")
            evidence.append(EvidenceItem(category="microstructure", point="Bid queue imbalance", weight=1.3, is_bullish=True))
        elif liq.depth_imbalance < -0.08:
            bearish.append(f"Negative order book depth imbalance ({liq.depth_imbalance*100:.1f}% ask side)")
            evidence.append(EvidenceItem(category="microstructure", point="Ask queue pressure", weight=1.2, is_bullish=False))

        net_score = len(bullish) - len(bearish)
        if net_score >= 1 and liq.bid_ask_spread_bps <= 8.0:
            signal = AgentSignalType.BUY
            confidence = min(0.85, max(0.60, 0.65 + 0.08 * net_score))
        elif net_score <= -1:
            signal = AgentSignalType.SELL if net_score <= -2 else AgentSignalType.HOLD
            confidence = min(0.80, max(0.55, 0.60 + 0.08 * abs(net_score)))
        else:
            signal = AgentSignalType.HOLD
            confidence = 0.50

        return AgentOutput(
            agent=self.name,
            symbol=context.symbol,
            signal=signal,
            confidence=round(confidence, 2),
            expected_return=0.02 if signal == AgentSignalType.BUY else 0.0,
            expected_risk=0.01,
            holding_period_days=2,
            reasoning=f"Microstructure: Spread {liq.bid_ask_spread_bps:.1f} bps, Depth Imbalance {liq.depth_imbalance*100:+.1f}%.",
            bullish_points=bullish,
            bearish_points=bearish,
            evidence=evidence,
            risk_flags=risk_flags,
            features_used=features_used,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            metrics={"spread_bps": liq.bid_ask_spread_bps, "depth_imbalance": liq.depth_imbalance, "turnover": liq.turnover_ratio},
        )


# ==========================================
# Legacy Aliases for Compatibility
# ==========================================
SentimentAgent = SentimentNewsAgent
ResearchAgent = SentimentNewsAgent
OptionsAgent = QuantAgent
CrossAssetAgent = MacroAgent
PatternDiscoveryAgent = TechnicalAgent
SimulationAgent = QuantAgent
ComplianceAgent = MacroAgent
CostAnalysisAgent = MicrostructureAgent
DataQualityAgent = TechnicalAgent
