"""
ATHENA Multi-Agent AI Quantitative Trading Platform - Main API Gateway
"""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from packages.common.config import settings
from packages.database.session import init_db
from packages.logging.logger import correlation_id_ctx, get_logger
from packages.monitoring.metrics import metrics

# Import all domain routers
from apps.api.routers.agents import router as agents_router
from apps.api.routers.auth import router as auth_router
from apps.api.routers.backtests import router as backtests_router
from apps.api.routers.debates import router as debates_router
from apps.api.routers.decisions import router as decisions_router
from apps.api.routers.journal import router as journal_router
from apps.api.routers.learning import router as learning_router
from apps.api.routers.markets import router as markets_router
from apps.api.routers.orders import router as orders_router
from apps.api.routers.portfolio import router as portfolio_router
from apps.api.routers.regime import router as regime_router
from apps.api.routers.risk import router as risk_router
from apps.api.routers.strategies import router as strategies_router
from apps.api.routers.websocket import router as websocket_router

logger = get_logger("athena.api_gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ATHENA Autonomous Hedge Fund Operating System...")
    await init_db()
    logger.info("Database schemas verified.")
    yield
    logger.info("Shutting down ATHENA platform safely.")


app = FastAPI(
    title="ATHENA Quantitative Operating System",
    description="Production-Grade Multi-Agent AI Quantitative Trading and Research Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    token = correlation_id_ctx.set(corr_id)
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response
    finally:
        correlation_id_ctx.reset(token)


# Health & Status Endpoint
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "OPERATIONAL",
        "platform": "ATHENA",
        "live_trading_enabled": settings.LIVE_TRADING_ENABLED,
        "execution_mode": settings.EXECUTION_MODE,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


# Prometheus Metrics Endpoint
@app.get("/metrics", tags=["System"])
async def prometheus_metrics():
    return PlainTextResponse(metrics.get_prometheus_metrics())


# Mount All Feature Routers
app.include_router(auth_router)
app.include_router(markets_router)
app.include_router(agents_router)
app.include_router(strategies_router)
app.include_router(regime_router)
app.include_router(debates_router)
app.include_router(decisions_router)
app.include_router(risk_router)
app.include_router(portfolio_router)
app.include_router(orders_router)
app.include_router(backtests_router)
app.include_router(learning_router)
app.include_router(journal_router)
app.include_router(websocket_router)
