"""
ATHENA SQLAlchemy 2.0 Relational & Time-Series Models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ==========================================
# 1. AUTH & SECURITY
# ==========================================
class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="VIEWER", nullable=False)  # ADMIN, RESEARCHER, TRADER, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ==========================================
# 2. MARKET DATA & ASSETS
# ==========================================
class AssetModel(Base):
    __tablename__ = "assets"

    symbol = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    asset_class = Column(String(30), default="EQUITY")
    sector = Column(String(50), default="Technology")
    currency = Column(String(10), default="USD")
    tick_size = Column(Float, default=0.01)
    lot_size = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketCandleModel(Base):
    __tablename__ = "market_candles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(20), ForeignKey("assets.symbol"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    vwap = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_candle_sym_time", "symbol", "timestamp", unique=True),
    )


# ==========================================
# 3. QUANTITATIVE FEATURES & REGIMES
# ==========================================
class FeatureSnapshotModel(Base):
    __tablename__ = "feature_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(20), ForeignKey("assets.symbol"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    current_price = Column(Float, nullable=False)
    technical_features = Column(JSON, nullable=False)
    statistical_features = Column(JSON, nullable=False)
    volatility_features = Column(JSON, nullable=False)
    liquidity_features = Column(JSON, nullable=False)
    options_features = Column(JSON, nullable=False)
    cross_asset_features = Column(JSON, nullable=False)
    nlp_features = Column(JSON, nullable=False)


class MarketRegimeModel(Base):
    __tablename__ = "market_regimes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    symbol_or_market = Column(String(20), default="SPY", index=True)
    regime = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    recommended_strategies = Column(JSON, nullable=True)
    strategy_suitability_weights = Column(JSON, nullable=True)
    ensemble_breakdown = Column(JSON, nullable=True)


# ==========================================
# 4. AI AGENTS & STRATEGIES
# ==========================================
class AgentOutputModel(Base):
    __tablename__ = "agent_outputs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    signal = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    calibrated_probability = Column(Float, nullable=True)
    expected_return = Column(Float, default=0.0)
    expected_risk = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=False)
    bullish_points = Column(JSON, nullable=True)
    bearish_points = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    risk_flags = Column(JSON, nullable=True)
    model_version = Column(String(50), default="gpt-4o")
    latency_ms = Column(Integer, default=0)


class StrategyOutputModel(Base):
    __tablename__ = "strategy_outputs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    signal = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    expected_return = Column(Float, default=0.0)
    expected_drawdown = Column(Float, default=0.0)
    holding_period = Column(String(20), default="5D")
    rationale = Column(Text, nullable=True)


# ==========================================
# 5. DEBATES, DECISIONS & RISK CHECKS
# ==========================================
class DebateModel(Base):
    __tablename__ = "debates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    agreement_score = Column(Float, nullable=False)
    conflicts = Column(JSON, nullable=True)
    strongest_bullish_evidence = Column(JSON, nullable=True)
    strongest_bearish_evidence = Column(JSON, nullable=True)
    debate_synthesis = Column(Text, nullable=False)
    recommended_action = Column(String(10), nullable=False)
    consensus_confidence = Column(Float, nullable=False)


class DecisionModel(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    calibrated_probability = Column(Float, nullable=True)
    current_price = Column(Float, nullable=False)
    target_weight = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    expected_return_pct = Column(Float, default=0.0)
    expected_drawdown_pct = Column(Float, default=0.0)
    risk_reward_ratio = Column(Float, default=2.0)
    regime = Column(String(30), default="BULL")
    reasoning = Column(Text, nullable=False)
    alternative_scenarios = Column(JSON, nullable=True)
    validation_status = Column(String(20), default="VALIDATED")


class RiskCheckModel(Base):
    __tablename__ = "risk_checks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    decision_id = Column(String(36), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    approved = Column(Boolean, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    max_approved_shares = Column(Integer, default=0)
    violations = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    veto_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# ==========================================
# 6. ORDERS, EXECUTIONS & JOURNAL
# ==========================================
class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_order_id = Column(String(50), unique=True, nullable=False, index=True)
    decision_id = Column(String(36), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), default="MARKET")
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0.0)
    limit_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    average_fill_price = Column(Float, nullable=True)
    status = Column(String(30), default="SUBMITTED", index=True)
    execution_mode = Column(String(10), default="PAPER", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FillModel(Base):
    __tablename__ = "fills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    slippage_bps = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class TradeJournalModel(Base):
    __tablename__ = "trade_journal"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    shares = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=True)
    realized_pnl_pct = Column(Float, nullable=True)
    status = Column(String(20), default="OPEN", index=True)
    regime_at_entry = Column(String(30), nullable=False)
    confidence_at_entry = Column(Float, nullable=False)
    predicted_return = Column(Float, default=0.0)
    actual_return = Column(Float, nullable=True)
    decision_snapshot = Column(JSON, nullable=False)
    risk_check_snapshot = Column(JSON, nullable=False)
    explainability_report_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ==========================================
# 7. BACKTESTS & LEARNING
# ==========================================
class BacktestRunModel(Base):
    __tablename__ = "backtest_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), default="Backtest Run")
    config = Column(JSON, nullable=False)
    status = Column(String(20), default="COMPLETED")
    metrics = Column(JSON, nullable=False)
    equity_curve = Column(JSON, nullable=False)
    monthly_returns = Column(JSON, nullable=True)
    regime_performance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningRunModel(Base):
    __tablename__ = "learning_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    trades_analyzed = Column(Integer, default=0)
    overall_win_rate = Column(Float, default=0.0)
    agent_weight_updates = Column(JSON, nullable=False)
    strategy_weight_updates = Column(JSON, nullable=False)
    calibration_metrics = Column(JSON, nullable=False)
    insights = Column(Text, nullable=True)
    approval_status = Column(String(40), default="PENDING_OPERATOR_APPROVAL")
    created_at = Column(DateTime, default=datetime.utcnow)
