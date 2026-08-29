# ATHENA REST & WebSocket API Specification

## Base URL
`http://localhost:8000`

---

## 1. Authentication
* `POST /auth/login` - Authenticate with username & password; returns access & refresh tokens.
* `POST /auth/refresh` - Refresh access token.
* `GET /auth/me` - Get profile of authenticated user.

## 2. Markets & Universe
* `GET /markets` - List active asset universe.
* `GET /markets/{symbol}` - Real-time market tick and quotes.
* `GET /markets/{symbol}/candles` - Historical OHLCV candle bars.
* `GET /markets/{symbol}/orderbook` - L2 Order book depth snapshot.
* `GET /markets/{symbol}/features` - Extracted multidimensional quantitative feature snapshot.

## 3. AI Agents
* `GET /agents` - List all 14 registered AI agents.
* `GET /agents/{agent_name}` - Details and model version for specific agent.
* `POST /agents/{agent_name}/analyze?symbol=AAPL` - Execute analysis for a specific agent.
* `POST /agents/run-all?symbol=AAPL` - Execute all 14 agents concurrently and return summary.

## 4. Quantitative Strategies
* `GET /strategies` - List all 16 strategies.
* `POST /strategies/run-all?symbol=AAPL` - Run all 16 strategies on market context.

## 5. Market Regime
* `GET /regime/current?symbol=SPY` - Current ensemble market regime state.

## 6. Debate Engine
* `POST /debates/generate?symbol=AAPL` - Trigger multi-agent dialectical debate.

## 7. Decision Engine
* `GET /decisions` - Get list of recent structured decisions from memory.
* `POST /decisions/generate?symbol=AAPL` - Generate validated trading decision.

## 8. Risk Management
* `GET /risk/status` - Current portfolio exposure, VaR, CVaR, and risk health.
* `GET /risk/limits` - Configured institutional risk boundaries.
* `POST /risk/check` - Evaluate a proposed decision against all risk rules.
* `POST /risk/kill-switch` - Emergency platform-wide execution halt.
* `POST /risk/kill-switch/reset` - Operator kill-switch reset.

## 9. Portfolio
* `GET /portfolio` - Total NAV, cash, gross exposure, and PnL.
* `GET /portfolio/positions` - Active open positions.
* `POST /portfolio/optimize` - Run convex portfolio optimization (MPT, Risk Parity, Kelly, CVaR).

## 10. Orders & Execution
* `GET /orders` - List all submitted orders and fills.
* `POST /orders/execute-decision` - Execute a structured decision through the full deterministic pipeline.
* `POST /orders/paper` - Submit paper order.
* `POST /orders/live` - Submit live order (Blocked if `LIVE_TRADING_ENABLED=false`).

## 11. Backtesting & Learning
* `POST /backtests` - Submit event-driven backtest configuration.
* `GET /learning/weights` - Current Bayesian agent and strategy weights.
* `GET /learning/calibration` - Platt scaling calibration curves and Brier scores.
* `POST /learning/run` - Trigger offline learning cycle on closed trades.

## 12. Trade Journal
* `GET /journal` - List all historical trade entries.
* `GET /journal/{trade_id}` - Detailed trade entry snapshot.
* `GET /journal/{trade_id}/explainability` - Rendered Markdown Trade Explainability Report.

## 13. WebSockets
* `WS /ws/stream` - Real-time event bus stream for ticks, agent signals, risk alerts, orders, and fills.
