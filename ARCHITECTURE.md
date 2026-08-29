# ATHENA Architecture Specification

## 1. System Overview
ATHENA is a modular, event-driven multi-agent quantitative hedge fund operating system designed for deterministic research, backtesting, paper execution, and safety-audited live trading.

```
                               ┌─────────────────────────────┐
                               │  Market Data Ingestion Bus  │
                               │  (Alpaca, NSE, Polygon)     │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │   Data Quality Gate (DQA)   │
                               │   (Score Threshold >= 0.80) │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │  Feature Engineering Matrix │
                               │  (Technical, Vol, Alpha)    │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ Market Regime Classifier    │
                               │ (HMM / GMM / Vol Ensemble)  │
                               └──────────────┬──────────────┘
                                              │
                 ┌────────────────────────────┴────────────────────────────┐
                 │                                                         │
                 ▼                                                         ▼
  ┌─────────────────────────────┐                           ┌─────────────────────────────┐
  │   14 AI Analytical Agents   │                           │  16 Quantitative Strategies │
  │   - Technical Agent         │                           │  - Trend Following          │
  │   - Quantitative Alpha      │                           │  - Statistical Arbitrage    │
  │   - Fundamental Analyst     │                           │  - Mean Reversion           │
  │   - Macro & Sentiment       │                           │  - ML LightGBM / RL PPO     │
  │   - Microstructure & Options│                           │  - Risk Parity & Momentum   │
  └──────────────┬──────────────┘                           └──────────────┬──────────────┘
                 │                                                         │
                 └────────────────────────────┬────────────────────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │  Dialectical Debate Engine  │
                               │  (Bull vs Bear Synthesis)   │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ Empirical Evidence Validator│
                               │ (Statistical Edge Guard)    │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ Quantitative Decision Engine│
                               │ (Action, Target, SL/TP)     │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ Risk Management VETO Layer  │
                               │ (Hard Institutional Bounds) │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ Deterministic Router        │
                               │ (Alpaca Paper / Live API)   │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ 4-Tier Memory & Trade Audit │
                               │ (Markdown Audit Trails)     │
                               └─────────────────────────────┘
```

---

## 2. Directory Structure

```text
├── apps/
│   └── api/                    # FastAPI Institutional REST & WebSocket Gateway
│       ├── routers/            # 14 specialized endpoint routers
│       └── main.py             # Application factory & middleware
├── packages/
│   ├── common/                 # Core settings, exceptions, and security
│   ├── database/               # Async SQLAlchemy ORM & TimescaleDB models
│   ├── event_bus/              # PubSub event messaging
│   ├── logging/                # Structured JSON logging & correlation IDs
│   ├── memory/                 # Ephemeral, short, long-term, and entity memory
│   ├── monitoring/             # Prometheus metrics registry
│   └── schemas/                # Strongly-typed Pydantic schemas
├── services/
│   ├── agent_service/          # 14 AI analytical agent implementations & LLM Gateway
│   ├── backtesting_service/    # Zero-lookahead event-driven backtesting engine
│   ├── data_service/           # Data quality agent & market data providers (Alpaca, NSE)
│   ├── debate_service/         # Dialectical bull/bear debate engine
│   ├── decision_service/       # Confidence-weighted decision synthesizer
│   ├── execution_service/      # Alpaca Paper adapter, live broker, deterministic router
│   ├── feature_service/        # Feature extraction pipeline (RSI, MACD, Volatility)
│   ├── journal_service/        # Automated Markdown Trade Explainability Logger
│   ├── learning_service/       # Post-trade retrospective feedback loop
│   ├── portfolio_service/      # Convex portfolio optimizer (Markowitz, Risk Parity)
│   ├── regime_service/         # Gaussian HMM & GMM market regime detector
│   ├── risk_service/           # Independent unilateral Risk Management VETO Layer
│   └── strategy_service/       # 16 institutional quantitative strategies
├── scripts/                    # CLI execution runners & market bots
│   ├── run_alpaca_live.py      # Alpaca Paper Trading runner
│   ├── run_continuous_alpaca.py# 24/7 continuous autonomous universe scanner
│   ├── run_indian_market_daily_bot.py # Daily Indian market scanner & execution bot
│   ├── run_backtest.py         # Historical event-driven simulation lab
│   └── seed_data.py            # Database seeder
├── tests/                      # Automated test suite (Unit, Integration, Failure-Injection)
├── docker-compose.yml          # TimescaleDB, Redis, Kafka, API stack
└── pyproject.toml              # Project dependencies & build metadata
```

---

## 3. Core Principles

1. **Deterministic Risk Precedence**: No agent or LLM has unilateral execution authority. Every decision MUST clear the independent Risk Management VETO Layer.
2. **Empirical Edge Validation**: Agents must cite numerical evidence (Sharpe ratio, historical edge, Z-scores) during dialectical debate.
3. **Zero Look-Ahead Bias**: The backtesting engine enforces strict timestamp sequencing.
4. **Safety by Default**: `LIVE_TRADING_ENABLED=false` and `EXECUTION_MODE=PAPER` are enforced at code, schema, and API levels.
