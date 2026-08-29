# ATHENA Database Schema & Time-Series Design

## Database Architecture
ATHENA uses PostgreSQL with TimescaleDB for time-series tick/bar persistence and pgvector for semantic trade search.

---

## Core Relational Tables

1. `users` - User credentials, hashed password, role (ADMIN, RESEARCHER, TRADER, VIEWER).
2. `audit_logs` - Immutable compliance log of user actions and IP addresses.
3. `assets` - Universe asset definitions, lot size, tick size, sector.
4. `market_candles` - TimescaleDB hypertable storing OHLCV candles partitioned by `timestamp`.
5. `feature_snapshots` - Historical quantitative feature vector snapshots.
6. `market_regimes` - Detected market regime history and ensemble breakdown.
7. `agent_outputs` - Structured outputs from 14 AI agents with tokens and latency.
8. `strategy_outputs` - Structured signals from 16 quantitative strategies.
9. `debates` - Multi-agent debate transcripts, conflicts, and agreement scores.
10. `decisions` - Final synthesized decisions with alternative scenarios and stop loss/take profit.
11. `risk_checks` - Veto audits, violations, and risk score snapshots.
12. `orders` - Deterministic order requests, status, execution mode (PAPER/LIVE).
13. `fills` - Real-time execution fills with fees, slippage, and liquidity type.
14. `trade_journal` - Full trade lifecycle with embedded Markdown Explainability Reports.
15. `backtest_runs` - Historical backtest execution configs and metrics.
16. `learning_runs` - Offline Bayesian updates and calibration metrics.
