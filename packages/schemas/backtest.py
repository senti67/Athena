"""
ATHENA Event-Driven Backtesting Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    backtest_id: str = "bt-default"
    symbols: List[str] = Field(default_factory=lambda: ["AAPL", "NVDA", "MSFT", "SPY"])
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    initial_cash: float = 100000.0
    slippage_bps: float = 5.0
    commission_per_share: float = 0.005
    strategies_enabled: List[str] = Field(default_factory=lambda: ["trend_following", "momentum", "mean_reversion"])
    use_multi_agent_consensus: bool = True
    regime_filter_enabled: bool = True
    risk_veto_enabled: bool = True


class BacktestMetrics(BaseModel):
    total_return_pct: float = 0.325
    cagr: float = 0.325
    sharpe_ratio: float = 1.85
    sortino_ratio: float = 2.40
    calmar_ratio: float = 3.65
    max_drawdown_pct: float = 0.089
    win_rate: float = 0.62
    profit_factor: float = 2.15
    expectancy: float = 0.012
    total_trades: int = 142
    winning_trades: int = 88
    losing_trades: int = 54
    avg_win_return: float = 0.045
    avg_loss_return: float = -0.018
    avg_holding_period_days: float = 4.2
    var_95: float = 0.018
    cvar_95: float = 0.027
    annualized_volatility: float = 0.142
    turnover_annual: float = 4.5


class MonteCarloSimulationResult(BaseModel):
    simulations_count: int = 1000
    median_cagr: float = 0.31
    percentile_5th_cagr: float = 0.12
    percentile_95th_cagr: float = 0.52
    median_max_drawdown: float = 0.095
    percentile_95th_max_drawdown: float = 0.165
    probability_of_ruin: float = 0.0001
    equity_paths_percentiles: Dict[str, List[float]] = Field(default_factory=dict)


class BacktestResult(BaseModel):
    backtest_id: str
    config: BacktestConfig
    status: str = "COMPLETED"  # RUNNING, COMPLETED, FAILED
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime = Field(default_factory=datetime.utcnow)
    metrics: BacktestMetrics
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list)  # [{date: ..., nav: ..., drawdown: ...}]
    monthly_returns_heatmap: Dict[str, Dict[str, float]] = Field(default_factory=dict)  # {year: {month: return}}
    regime_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    monte_carlo: Optional[MonteCarloSimulationResult] = None
    trades_sample: List[Dict[str, Any]] = Field(default_factory=list)
