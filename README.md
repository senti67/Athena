# ATHENA: Institutional Multi-Agent AI Quantitative Trading Platform

![ATHENA Banner](https://img.shields.io/badge/ATHENA-Autonomous%20Quantitative%20OS-06b6d4?style=for-the-badge)
![Alpaca](https://img.shields.io/badge/Alpaca%20Trading-Paper%20API%20v2-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![CI](https://img.shields.io/badge/CI%2FCD-Passing-brightgreen?style=for-the-badge)

ATHENA is an institutional-grade, multi-agent quantitative hedge fund operating system that analyzes live equity/crypto markets and executes deterministic paper and live trades directly through **Alpaca Markets Trading API (`https://paper-api.alpaca.markets/v2`)** and Indian equity market adapters.

All trades, orders, positions, and portfolio equity are synchronized with your official **[Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)**.

---

## 🏛 Core Architectural Pipeline

```text
Market Ingestion (Alpaca Data API / NSE / Polygon)
       │
       ▼
Data Quality Agent (DQA Score Threshold >= 0.80)
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

## 🧠 14 Specialized AI Agents

1. **Technical Analysis Agent**: Multi-timeframe trend & momentum analysis.
2. **Quantitative Alpha Agent**: Statistical mean-reversion, factor z-scores, Hurst exponents.
3. **Fundamental Analyst Agent**: Earnings quality, ROE, valuation multiples, margin trends.
4. **Sentiment Agent**: News sentiment, social momentum, NLP scoring.
5. **Macro Economic Agent**: Yield curve, inflation regime, interest rate differentials.
6. **Microstructure & Order Book Agent**: Bid-ask spread, order book imbalance, liquidity depth.
7. **Options & Volatility Surface Agent**: Implied vs. realized volatility, gamma exposure (GEX).
8. **Cross-Asset Correlation Agent**: Inter-market commodity, currency, and bond correlations.
9. **Pattern Discovery Agent**: Chart pattern recognition and candlestick formations.
10. **Simulation & Stress Test Agent**: Monte Carlo path simulations and tail-risk stress tests.
11. **Compliance & Regulatory Agent**: Wash sale prevention, short-sale restrictions, regulatory audits.
12. **Cost Analysis Agent**: Slippage modeling, spread costs, fee optimization.
13. **Data Quality Agent**: Price anomaly rejection, stale feed detection.
14. **Research Synthesis Agent**: Meta-analysis and dialectical debate coordination.

---

## 📈 16 Quantitative Strategy Models

* **Trend Following**: Multi-timeframe Moving Average / Donchian breakout.
* **Momentum**: Relative Strength Index (RSI) & Cross-Sectional momentum.
* **Mean Reversion**: Bollinger Band & Statistical Z-Score mean reversion.
* **Statistical Arbitrage**: Cointegration & Pairs Trading engine.
* **Sector Rotation**: Factor-weighted cross-sector momentum.
* **Machine Learning Alpha**: LightGBM gradient boosting model.
* **Reinforcement Learning**: Proximal Policy Optimization (PPO) agent.
* **Volatility Breakout**: ATR Volatility expansion and contraction.
* **Event-Driven & News**: NLP catalyst-based trading.
* **Convex Portfolio Optimizer**: Markowitz Mean-Variance, Risk Parity, Kelly Criterion, Min CVaR.

---

## ⚡ Quick Start: Running the Platform

### 1. Configure Your Alpaca API Keys
In your `.env` file (copied from `.env.example`):
```env
ALPACA_API_KEY=PKHJWVKWNNY6TQOLT75LL5YUFW
ALPACA_SECRET_KEY=8NFk6XedzahPHKeeLkxGGPhu65S1cp5GwAaT2g219MCF
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets
ALPACA_PAPER=true
BROKER_PROVIDER=alpaca
```

### 2. Run Single Asset Trading Cycle
```powershell
py scripts/run_alpaca_live.py AAPL
py scripts/run_alpaca_live.py NVDA
py scripts/run_alpaca_live.py TSLA
```

### 3. Run Continuous Autonomous Market Scanner
```powershell
py scripts/run_continuous_alpaca.py
```

### 4. Run Daily Indian NSE Market Bot
```powershell
py scripts/run_indian_market_daily_bot.py
```

### 5. Run Event-Driven Backtesting Lab
```powershell
py scripts/run_backtest.py
```

### 6. Run Automated Pytest Test Suite
```powershell
py -m pytest tests/ -v
```

### 7. Start the FastAPI Production Gateway
```powershell
py -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```
* **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Real-Time WebSocket Stream**: `ws://localhost:8000/ws/stream`
* **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 🛡️ Risk Management & Safety Controls

* **Unilateral Risk VETO**: All decisions must clear position caps, $5,000 max daily loss, 15% drawdown limits, and data quality checks before reaching broker execution.
* **Master Live Switch**: Live execution is disabled by default (`LIVE_TRADING_ENABLED=false`, `EXECUTION_MODE=PAPER`).
* **Emergency Kill Switch**: Instantly freezes all broker order placement upon command.

---

## 📊 Live Trade Dashboard
Monitor live orders, filled executions, active portfolio positions, and NAV in real-time:
👉 **[https://app.alpaca.markets/paper/dashboard/overview](https://app.alpaca.markets/paper/dashboard/overview)**
