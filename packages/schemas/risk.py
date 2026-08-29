"""
ATHENA Independent Risk Management Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLimits(BaseModel):
    max_daily_loss: float = 5000.0
    max_position_size: float = 50000.0
    min_buying_power_reserve: float = 200000.0  # Hard floor of $200,000 buying power
    max_portfolio_exposure: float = 1.0  # 100%
    max_single_asset_exposure: float = 0.10  # 10%
    max_sector_concentration: float = 0.25  # 25%
    max_leverage: float = 1.0
    max_drawdown_limit: float = 0.15  # 15%
    var_95_limit: float = 0.03  # 3% 1-day VaR
    cvar_95_limit: float = 0.05  # 5% 1-day CVaR
    min_risk_reward_ratio: float = 1.5
    min_data_quality_score: float = 0.80


class RiskViolation(BaseModel):
    rule_name: str
    limit_value: float
    current_or_projected_value: float
    message: str
    severity: str = "CRITICAL"  # CRITICAL (triggers veto), WARNING


class RiskMetrics(BaseModel):
    portfolio_nav: float = 100000.0
    current_cash: float = 100000.0
    current_gross_exposure: float = 0.0
    current_net_exposure: float = 0.0
    current_leverage: float = 0.0
    daily_realized_pnl: float = 0.0
    daily_unrealized_pnl: float = 0.0
    current_drawdown_pct: float = 0.0
    historical_var_95: float = 0.015
    parametric_var_95: float = 0.016
    cvar_95_expected_shortfall: float = 0.025
    portfolio_volatility_annual: float = 0.14
    sharpe_ratio: float = 1.45
    beta_to_sp500: float = 0.85
    liquidity_score: float = 0.95


class RiskCheckResult(BaseModel):
    check_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision_id: str
    symbol: str
    action: str
    approved: bool
    risk_score: float = Field(ge=0.0, le=1.0, description="Overall risk index, lower is safer")
    max_approved_shares: int = 0
    max_approved_dollar_amount: float = 0.0
    violations: List[RiskViolation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    veto_reason: Optional[str] = None
    kill_switch_triggered: bool = False
    metrics_snapshot: RiskMetrics = Field(default_factory=RiskMetrics)
