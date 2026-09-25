# ATHENA: Autonomous Multi-Agent Quantitative Trading Platform

![ATHENA Banner](https://img.shields.io/badge/ATHENA-Autonomous%20Quantitative%20OS-06b6d4?style=for-the-badge)
![Alpaca](https://img.shields.io/badge/Alpaca%20Trading-Paper%20API%20v2-yellow?style=for-the-badge)
![Finnhub](https://img.shields.io/badge/Finnhub-Market%20Data%20API-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?style=for-the-badge)
![Telegram](https://img.shields.io/badge/Telegram-Real--Time%20Alerts-2CA5E0?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-27%2F27%20Passing-brightgreen?style=for-the-badge)

**ATHENA** is an institutional-grade, multi-agent quantitative trading system that automates the complete hedge fund lifecycle: live multi-provider market ingestion, regime classification, directional multi-agent research, dialectical debate synthesis, quantitative strategy scoring, strict multi-gate risk filtering, and deterministic order execution via the **Alpaca Markets API (`https://paper-api.alpaca.markets/v2`)**.

Real-time trade telemetry, position scorecards, and daily market digests are streamed directly to Telegram via **`@AthenaAnalysis_bot`**.

---

## 🏛 System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MULTI-PROVIDER DATA INGESTION                         │
│   • Alpaca Market Data v2 (Real-Time Quotes & Historical Bars)               │
│   • Finnhub REST API v1 (Fundamentals, News Sentiment, Metrics)             │
│   • 89-Asset Global Multi-Sector Watchlist (12 Industry Sectors)            │
│   • 55 req/min Token-Bucket Rate Limiter & Multi-Tier TTL Caches            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FEATURE & REGIME DETECTION ENGINE                       │
│   • Technical & Stat Indicators: EMA (9/21/50/200), RSI, MACD, ATR, Vol     │
│   • Market Regime Classifier: Trending Bull/Bear, Mean-Reverting, Ranging   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      6 DIRECTIONAL RESEARCH AGENTS                          │
│   [Technical]      [Quant Alpha]    [Fundamental]                           │
│   [News Sentiment] [Macro Regime]   [Microstructure]                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      5 ACTIVE PRODUCTION STRATEGIES                         │
│   1. Trend Following      2. RSI Momentum        3. Bollinger Mean-Rev      │
│   4. Sector Momentum      5. ATR Volatility Breakout                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SYNTHESIS & DECISION ENGINE                             │
│   • Dialectical Debate Protocol (Bull vs Bear Consensus & Friction Scoring) │
│   • Confidence-Weighted Conviction Scoring: Agreement % × Conviction × R:R  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  MULTI-GATE RISK MANAGEMENT & VETO LAYER                    │
│   • Max Position Cap: 20% NAV per asset (Kelly & Volatility scaled)         │
│   • Max Daily Loss Limit: $5,000 | Max Drawdown Ceiling: 15%                │
│   • Minimum Liquidity Floor: $20,000 Cash Reserve Buffer                    │
│   • Unilateral Risk VETO (Overrides any BUY/SELL signal unconditionally)    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EXECUTION ROUTER & NOTIFICATIONS                        │
│   • Alpaca Paper Trading API v2 (Deterministic Order Routing & Fills)       │
│   • Telegram Bot (@AthenaAnalysis_bot) Real-Time Alerts & 2-Hour Digests    │
│   • Automated Trade Journaling & State Persistence                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 6 Core Directional Research Agents

Each symbol undergoes concurrent multi-perspective research evaluated against live market metrics:

1. **Technical Analysis Agent**: Multi-timeframe trend structure, moving average alignment (9/21/50/200 EMA), momentum convergence, and key support/resistance boundaries.
2. **Quantitative Alpha Agent**: Statistical mean-reversion, rolling volatility percentiles, z-score deviations, and risk-reward profile estimation.
3. **Fundamental Valuation Agent**: Live metrics from Finnhub API (P/E, P/B, ROE, debt-to-equity ratios, operating margin trends, 52-week price percentiles).
4. **News Sentiment & NLP Agent**: Real-time corporate news ingestion, sentiment polarity scoring, catalyst identification, and headline buzz detection.
5. **Macroeconomic Environment Agent**: Broader market regime alignment, sector rotation tailwinds, index beta, and risk-on / risk-off environment filtering.
6. **Microstructure & Order Book Agent**: Spread analysis, liquidity depth, average daily volume qualification, and execution slippage impact.

---

## 📈 5 Active Production Strategies

Signals are generated and filtered through dynamic regime weighting:

* **Multi-Timeframe Trend Following**: Captures sustained directional trends using exponential moving average golden crosses and momentum confirmation.
* **Cross-Sectional RSI Momentum**: Identifies momentum surges and continuation setups in strong trending environments.
* **Bollinger Band Mean Reversion**: Exploits statistical overextension at 2.0+ standard deviation bands during range-bound regimes.
* **Sector-Relative Momentum**: Ranks relative performance across industry peers and selects high-conviction leaders.
* **ATR Volatility Breakout**: Captures volatility expansions following low-volatility consolidation compressions.

*(Experimental and high-drawdown strategies are safely quarantined in staging).*

---

## 🌐 89-Asset Global Multi-Sector Universe

Athena scans a comprehensive **89-asset multi-sector universe** across 12 distinct industries:

| Sector | Tickers |
| :--- | :--- |
| **Mega-Cap Technology** | `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `META`, `TSLA` |
| **Semiconductors & AI** | `NVDA`, `AMD`, `AVGO`, `QCOM`, `TSM`, `INTC`, `ARM`, `ASML`, `MU`, `MRVL` |
| **Cloud & Enterprise SaaS** | `CRM`, `ORCL`, `NOW`, `PLTR`, `SNOW`, `ADBE`, `PANW`, `CRWD`, `DDOG` |
| **Consumer & Retail Brands** | `NKE`, `SBUX`, `MCD`, `COST`, `WMT`, `TGT`, `LULU`, `HD`, `KO`, `PEP` |
| **Media, Gaming & Entertainment** | `DIS`, `NFLX`, `SPOT`, `EA`, `TTWO`, `SONY` |
| **Financials & FinTech** | `JPM`, `BAC`, `GS`, `MS`, `V`, `MA`, `PYPL`, `SQ`, `COIN` |
| **Healthcare & Pharmaceuticals** | `LLY`, `JNJ`, `UNH`, `PFE`, `MRK`, `ABBV`, `ISRG` |
| **Aerospace, Defense & Heavy Industry** | `BA`, `LMT`, `RTX`, `CAT`, `DE`, `GE` |
| **Energy & Clean Tech** | `XOM`, `CVX`, `COP`, `NEE`, `ENPH`, `FSLR` |
| **Automotive & Mobility** | `UBER`, `ABNB`, `F`, `GM`, `RIVN` |
| **Commodities, Indices & Crypto Proxies** | `SPY`, `QQQ`, `IWM`, `GLD`, `SLV`, `USO`, `IBIT`, `MSTR` |
| **Indian Equities & Bluechips (ADRs)** | `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY`, `WIT`, `IBN`, `TTM` |

---

## 🛡️ Institutional Risk Management & Capital Safeguards

All proposed trade decisions must pass through a strict **Multi-Gate Risk Engine** with unilateral veto authority:

* **Position Sizing Caps**: Maximum **20% NAV** per single symbol (scaled by volatility and Kelly allocation).
* **Portfolio Diversification**: Capital is rotated across uncorrelated sectors to avoid concentration.
* **Buying Power Reserve Floor**: Enforces a minimum **$20,000 cash reserve buffer** (or 20% of NAV) to prevent margin strain.
* **Drawdown & Loss Circuit Breakers**:
  * **$5,000 Max Daily Loss Limit**: Trading automatically halted if daily drawdown threshold is breached.
  * **15% Max Portfolio Drawdown**: Dynamic position trimming and portfolio de-risking.
* **Unilateral Risk VETO**: Risk engine can veto any agent or strategy recommendation without exception.
* **Master Safety Switches**: Live execution is gated behind `LIVE_TRADING_ENABLED=false` and `EXECUTION_MODE=PAPER`.

---

## ⚡ Multi-Provider Ingestion & Rate Limiting

Athena integrates with **Finnhub REST API v1** and **Alpaca Market Data v2**:

* **Token Bucket Rate Limiter**: Strictly capped at **55 calls/minute** (providing safe headroom below Finnhub's 60 calls/min free limit).
* **Multi-Tier TTL In-Memory Caching**:
  * **Company Fundamentals & Metrics**: 1 Hour TTL
  * **News & Market Sentiment**: 15 Minutes TTL
  * **OHLCV Historical Candles**: 1 Minute TTL
  * **Live Real-Time Quotes**: 10 Seconds TTL
* **HTTP 429 Backoff**: Automatic retry backoff adhering to `Retry-After` response headers.

---

## 🚀 Quick Start & Execution

### 1. Configure Environment Variables
Copy `.env.example` to `.env` and enter your Alpaca and Finnhub API credentials:
```env
# Alpaca Paper Trading Credentials
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets
ALPACA_PAPER=true
BROKER_PROVIDER=alpaca

# Finnhub Market Data API
FINNHUB_API_KEY=your_finnhub_key

# Telegram Real-Time Telemetry
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 2. Run the Autonomous Master Orchestrator Daemon
Runs the complete production schedule with automated trading sessions, 2-hour holding progress cards, and 8:00 PM daily market digests:
```powershell
py scripts/start_athena.py
```

### 3. Run Scheduled 4x Daily Trading Session
Executes automated market scans at 09:30 AM, 11:30 AM, 01:30 PM, and 03:30 PM EST:
```powershell
py scripts/run_four_times_daily_bot.py
```

### 4. Single-Asset Deep Analysis & Execution
Run full multi-agent research and deterministic execution cycle on any symbol:
```powershell
py scripts/run_alpaca_live.py NVDA
py scripts/run_alpaca_live.py TSLA
py scripts/run_alpaca_live.py JNJ
```

### 5. Run Automated Test Suite
```powershell
py -m pytest tests/ -v
```

---

## 📱 Real-Time Telegram Telemetry

Athena publishes structured operational cards directly to Telegram:
* **Order Executions**: Entry price, quantity, stop-loss, take-profit, confidence score, and rationale.
* **Take-Profit & Stop-Loss Alerts**: Automatic notifications when exit conditions trigger.
* **2-Hour Holding Progress Cards**: Real-time position PnL, mark-to-market valuations, and cash balances.
* **Daily Market Digests**: End-of-day portfolio performance and market overview at 08:00 PM EST.

---

## 📊 Live Trade Dashboard

Track live orders, positions, fills, and account NAV in real time:
👉 **[Alpaca Paper Trading Dashboard](https://app.alpaca.markets/paper/dashboard/overview)**

---

## ⚖️ Disclaimer & License

This software is for educational, research, and paper-trading purposes only. Quantitative and algorithmic trading involves significant financial risk. Always test thoroughly in paper trading environments before considering real capital allocation.

Distributed under the **MIT License**.
