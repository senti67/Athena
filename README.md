# ATHENA: Multi-Agent AI Quantitative Trading Platform (Alpaca Paper API Integrated)

![ATHENA Banner](https://img.shields.io/badge/ATHENA-Autonomous%20Hedge%20Fund%20OS-06b6d4?style=for-the-badge)
![Alpaca](https://img.shields.io/badge/Alpaca%20Trading-Paper%20API%20v2-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688?style=for-the-badge)

ATHENA is an institutional-grade, multi-agent quantitative hedge fund operating system that analyzes live markets and executes deterministic paper and live trades directly through **Alpaca Markets Trading API (`https://paper-api.alpaca.markets/v2`)**.

All trades, orders, positions, and portfolio equity are synchronized with your official **[Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)**.

---

## 🏛 Core Architectural Pipeline

```text
Market Ingestion (Alpaca Data API / Polygon)
       │
       ▼
Data Quality Agent (DQA Score >= 0.80)
       │
       ▼
Quantitative Feature Engine (RSI, MACD, EMA 9/21/50/200, Realized Vol, Alpha)
       │
       ▼
Market Regime Detector (Gaussian HMM / GMM / Volatility Ensemble)
       │
       ▼
14 Specialized AI Agents ─── Parallel Execution ─── 16 Quantitative Strategies
       │                                                         │
       └─────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
                    Dialectical Debate Engine (Consensus Agreement & Conflicts)
                                 │
                                 ▼
                    Statistical Evidence Validator (Empirical Profit Margin)
                                 │
                                 ▼
                    Confidence-Weighted Decision Engine
                                 │
                                 ▼
                    Independent Risk Management VETO Layer (Unilateral Veto)
                                 │
                                 ▼
                    Alpaca Paper Trading API (https://paper-api.alpaca.markets/v2)
                                 │
                                 ▼
                    Alpaca Account Dashboard & Automated Trade Journal
```

---

## ⚡ Quick Start: Connecting Alpaca Paper Trading

### 1. Configure Your Alpaca API Keys
In your `.env` file (copied from `.env.example`):
```env
ALPACA_API_KEY=your_alpaca_api_key_id
ALPACA_SECRET_KEY=your_alpaca_api_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets
ALPACA_PAPER=true
BROKER_PROVIDER=alpaca
```

### 2. Run the Autonomous Multi-Agent Trading Cycle
To analyze an asset (e.g. `AAPL` or `NVDA`) and submit an autonomous order directly to your Alpaca account:
```bash
py scripts/run_alpaca_live.py AAPL
```

### 3. Run Event-Driven Backtesting Lab
```bash
py scripts/run_backtest.py
```

### 4. Run Automated Pytest Test Suite
```bash
py -m pytest tests/ -v
```

### 5. Start the FastAPI Main Gateway
```bash
py -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```
* **Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Real-time WebSocket Stream**: `ws://localhost:8000/ws/stream`
* **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 🛡️ Risk Management & Safety

* **Unilateral Risk VETO**: All decisions must clear position caps, $5,000 max daily loss, 15% drawdown limits, and data quality checks before reaching Alpaca.
* **Master Live Switch**: Live execution is disabled by default (`LIVE_TRADING_ENABLED=false`, `EXECUTION_MODE=PAPER`).
* **Emergency Kill Switch**: Instantly freezes all broker order placement.

---

## 📊 View Your Live Trades
All executed orders, fills, and active positions appear directly on your official Alpaca Paper Dashboard:
👉 **[https://app.alpaca.markets/paper/dashboard/overview](https://app.alpaca.markets/paper/dashboard/overview)**
