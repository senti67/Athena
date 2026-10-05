"""
ATHENA Standardized Trade Card & Notification Domain Models
Defines structured, strongly-typed data contracts for institutional Telegram research notes.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    TRADE_SIGNAL = "TRADE_SIGNAL"
    POSITION_UPDATE = "POSITION_UPDATE"
    NO_TRADE = "NO_TRADE"
    DAILY_REPORT = "DAILY_REPORT"
    RISK_VETO = "RISK_VETO"
    GENERAL_ALERT = "GENERAL_ALERT"


class Thesis(BaseModel):
    """Structured investment thesis for an executed or evaluated trade."""
    primary_driver: str = Field(..., description="Primary strategic or quantitative catalyst")
    secondary_driver: Optional[str] = Field(None, description="Secondary confirming factor")
    supporting_factors: List[str] = Field(default_factory=list, description="2-4 concrete factual reasons supporting the trade")
    risk_factors: List[str] = Field(default_factory=list, description="1-3 major risks and failure modes")
    invalidation_conditions: List[str] = Field(default_factory=list, description="Explicit price levels or regime shifts that invalidate thesis")


class StrategyContribution(BaseModel):
    """Contribution metric for a single quantitative strategy."""
    strategy_name: str
    signal: str = "HOLD"
    score: float = 0.0
    weight: float = 1.0
    material_contribution: bool = True


class RiskCheckResultCard(BaseModel):
    """Institutional risk guard verification status."""
    risk_per_trade_pct: Optional[float] = None
    portfolio_exposure_pct: Optional[float] = None
    daily_loss_limit_ok: bool = True
    buying_power_ok: bool = True
    position_limit_ok: bool = True
    correlation_risk_ok: bool = True
    data_quality_ok: bool = True
    approved: bool = True
    veto_reason: Optional[str] = None


class TradeCard(BaseModel):
    """
    Complete Trade Card data contract for a Trade Signal research note.
    All fields are populated from verified quantitative calculations.
    """
    symbol: str
    side: str = "BUY"  # BUY, SELL, SHORT, COVER
    decision: str = "BUY APPROVED"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Price & Targets
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # Sizing & Exposure
    position_size: Optional[float] = None  # Shares
    position_value: Optional[float] = None  # Dollar exposure
    portfolio_weight: Optional[float] = None  # % of portfolio NAV

    # Market Context & Regimes
    regime: str = "UNCERTAIN"
    regime_confidence: Optional[float] = None
    volatility_label: Optional[str] = "Moderate"
    trend_details: Optional[str] = None
    momentum_details: Optional[str] = None
    volume_details: Optional[str] = None

    # Quantitative Signals & Edge
    signal_score: float = 50.0  # 0 to 100
    confidence: float = 0.50
    expected_edge: Optional[float] = None  # e.g., 0.0184 -> +1.84%
    reward_risk: Optional[float] = None

    # Strategy Breakdown
    strategy_contributions: List[StrategyContribution] = Field(default_factory=list)

    # Thesis & Explanations
    thesis: Thesis
    risk_checks: RiskCheckResultCard = Field(default_factory=RiskCheckResultCard)
    decision_reason: Optional[str] = None
    execution_mode: str = "PAPER TRADE"
    order_id: Optional[str] = None


class PositionUpdateCard(BaseModel):
    """
    Data contract for ongoing position monitoring and health reports.
    """
    symbol: str
    side: str = "LONG"
    entry_price: float
    current_price: float
    shares: float
    unrealized_pnl_pct: float
    unrealized_pnl_val: float
    holding_duration_str: Optional[str] = "0h"
    original_thesis: Optional[str] = "Trend + Momentum"
    current_regime: str = "TRENDING BULL"
    momentum_status: str = "Neutral"
    volume_status: str = "Supportive"
    signal: str = "HOLD"
    thesis_strength_score: Optional[int] = None
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    dist_to_target_pct: Optional[float] = None
    dist_to_stop_pct: Optional[float] = None
    assessment_verdict: str = "HOLD"
    assessment_reason: str = "The original thesis remains valid. Momentum remains supportive."
    next_review_time: Optional[str] = "In 2 hours"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NoTradeCard(BaseModel):
    """
    Data contract explaining why Athena decided NOT to trade a candidate asset.
    """
    symbol: str
    candidate_signal: str = "BUY"
    final_score: int = 50
    required_score: int = 75
    trend_state: str = "Neutral"
    momentum_state: str = "Neutral"
    mean_reversion_state: str = "Neutral"
    volatility_state: str = "Normal"
    regime: str = "UNCERTAIN"
    blocking_factors: List[str] = Field(default_factory=list)
    decision_summary: str = "HOLD / NO TRADE"
    decision_detail: str = "Athena is waiting for stronger confirmation."
    next_triggers: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DailyReportCard(BaseModel):
    """
    Data contract for the daily performance summary.
    Every metric is Optional: None means "not measured" and is rendered as N/A (never defaulted).
    """
    date_str: str
    portfolio_value: Optional[float] = None
    daily_pnl_pct: Optional[float] = None
    daily_pnl_val: Optional[float] = None
    total_pnl_pct: Optional[float] = None
    total_pnl_val: Optional[float] = None
    trades_count: Optional[int] = None
    wins_count: Optional[int] = None
    losses_count: Optional[int] = None
    win_rate_pct: Optional[float] = None
    profit_factor: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    portfolio_exposure_pct: Optional[float] = None
    largest_position_str: Optional[str] = None
    daily_risk_pct: Optional[float] = None
    spy_regime: Optional[str] = None
    qqq_regime: Optional[str] = None
    vix_status: Optional[str] = None
    overall_market_bias: Optional[str] = None
    trades_executed: Optional[int] = None
    signals_rejected: Optional[int] = None
    risk_vetoes: Optional[int] = None
    most_successful_strategy: Optional[str] = None
    weakest_strategy: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
