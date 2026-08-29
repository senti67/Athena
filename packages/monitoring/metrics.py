"""
ATHENA Prometheus Observability & Metrics Engine
"""

import time
from typing import Dict
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Operational Metrics
ORDERS_TOTAL = Counter(
    "athena_orders_total",
    "Total orders submitted",
    ["symbol", "side", "status", "mode"],
)

FILLS_TOTAL = Counter(
    "athena_fills_total",
    "Total order fills received",
    ["symbol", "side"],
)

RISK_REJECTIONS_TOTAL = Counter(
    "athena_risk_rejections_total",
    "Total decisions vetoed by the risk engine",
    ["symbol", "rule_name"],
)

AGENT_LATENCY = Histogram(
    "athena_agent_latency_seconds",
    "Latency of AI analytical agent execution",
    ["agent_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

LLM_TOKENS_TOTAL = Counter(
    "athena_llm_tokens_total",
    "Total tokens consumed by LLM calls",
    ["agent", "model", "token_type"],  # token_type: prompt / completion
)

DATA_QUALITY_SCORE = Gauge(
    "athena_data_quality_score",
    "Current data quality score (0.0 to 1.0)",
    ["symbol"],
)

PORTFOLIO_NAV = Gauge(
    "athena_portfolio_nav_dollars",
    "Total portfolio Net Asset Value",
)

PORTFOLIO_DRAWDOWN = Gauge(
    "athena_portfolio_drawdown_ratio",
    "Current portfolio drawdown ratio",
)

MARKET_REGIME = Gauge(
    "athena_market_regime",
    "Current detected market regime",
    ["regime_name"],
)


class MetricsManager:
    """Helper class for recording latency and system metrics."""

    @staticmethod
    def record_order(symbol: str, side: str, status: str, mode: str = "PAPER"):
        ORDERS_TOTAL.labels(symbol=symbol, side=side, status=status, mode=mode).inc()

    @staticmethod
    def record_fill(symbol: str, side: str):
        FILLS_TOTAL.labels(symbol=symbol, side=side).inc()

    @staticmethod
    def record_risk_veto(symbol: str, rule: str):
        RISK_REJECTIONS_TOTAL.labels(symbol=symbol, rule_name=rule).inc()

    @staticmethod
    def update_portfolio_state(nav: float, drawdown: float):
        PORTFOLIO_NAV.set(nav)
        PORTFOLIO_DRAWDOWN.set(drawdown)

    @staticmethod
    def update_data_quality(symbol: str, score: float):
        DATA_QUALITY_SCORE.labels(symbol=symbol).set(score)

    @staticmethod
    def get_prometheus_metrics() -> bytes:
        return generate_latest()


metrics = MetricsManager()
