"""
ATHENA Feature Engineering Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TechnicalFeatures(BaseModel):
    rsi_14: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    ema_9: float = 0.0
    ema_21: float = 0.0
    ema_50: float = 0.0
    ema_200: float = 0.0
    sma_20: float = 0.0
    vwap: float = 0.0
    adx_14: float = 20.0
    atr_14: float = 1.5
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_bandwidth: float = 0.0
    stoch_k: float = 50.0
    stoch_d: float = 50.0
    pivot_support: float = 0.0
    pivot_resistance: float = 0.0
    volume_sma_20: float = 0.0
    volume_ratio: float = 1.0


class StatisticalFeatures(BaseModel):
    returns_1d: float = 0.0
    returns_5d: float = 0.0
    returns_20d: float = 0.0
    rolling_mean_20d: float = 0.0
    rolling_std_20d: float = 0.0
    z_score_20d: float = 0.0
    skewness_60d: float = 0.0
    kurtosis_60d: float = 3.0
    autocorr_lag1: float = 0.0
    beta_spy: float = 1.0
    alpha_annual: float = 0.0
    sharpe_60d: float = 1.0
    sortino_60d: float = 1.2


class VolatilityFeatures(BaseModel):
    realized_vol_20d: float = 0.15
    parkinson_vol_20d: float = 0.14
    atr_normalized: float = 0.015
    vol_regime_ratio: float = 1.0  # current vol / historical mean vol
    vol_clustering_index: float = 0.0


class LiquidityFeatures(BaseModel):
    bid_ask_spread_bps: float = 3.0
    depth_imbalance: float = 0.0
    volume_imbalance: float = 0.0
    amihud_illiquidity: float = 0.0001
    turnover_ratio: float = 0.02


class OptionsFeatures(BaseModel):
    implied_vol_30d: float = 0.20
    iv_rank: float = 45.0  # 0 to 100
    iv_percentile: float = 50.0
    put_call_ratio: float = 0.85
    gamma_exposure_gex: float = 1200000.0  # Proxy GEX
    option_sentiment_bias: float = 0.15  # -1 to +1


class CrossAssetFeatures(BaseModel):
    spy_return_1d: float = 0.002
    qqq_return_1d: float = 0.003
    tlt_return_1d: float = -0.001
    gld_return_1d: float = 0.001
    uso_return_1d: float = 0.0
    uup_dollar_return_1d: float = 0.0
    btc_return_1d: float = 0.01
    vix_level: float = 15.5
    vix_change_pct: float = -0.02
    risk_on_indicator: float = 0.65  # 0 (risk-off) to 1 (risk-on)


class NLPFeatures(BaseModel):
    sentiment_score: float = 0.25  # -1.0 to 1.0
    sentiment_magnitude: float = 0.70
    bullish_percentage: float = 0.60
    bearish_percentage: float = 0.20
    fear_greed_index: float = 65.0  # 0 to 100
    news_velocity: float = 1.2  # volume of news vs baseline
    key_events: List[str] = Field(default_factory=list)


class FeatureSnapshot(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    current_price: float
    technical: TechnicalFeatures = Field(default_factory=TechnicalFeatures)
    statistical: StatisticalFeatures = Field(default_factory=StatisticalFeatures)
    volatility: VolatilityFeatures = Field(default_factory=VolatilityFeatures)
    liquidity: LiquidityFeatures = Field(default_factory=LiquidityFeatures)
    options: OptionsFeatures = Field(default_factory=OptionsFeatures)
    cross_asset: CrossAssetFeatures = Field(default_factory=CrossAssetFeatures)
    nlp: NLPFeatures = Field(default_factory=NLPFeatures)
    raw_feature_map: Dict[str, float] = Field(default_factory=dict)
