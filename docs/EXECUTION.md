# ATHENA Deterministic Execution & Paper Broker Engine

## Deterministic Execution Pipeline
```text
Validated Decision -> Risk Veto Check -> Idempotency Check -> Broker Adapter -> Fills -> Portfolio & Journal
```

## Safety Controls
* **Live Trading Switch**: `LIVE_TRADING_ENABLED=false` by default. Live orders submitted while false throw `LiveTradingDisabledException`.
* **Realistic Paper Broker**:
  - Variable slippage proportional to market volatility and order size (default 5.0 bps).
  - Commission fee modeling ($0.005 per share).
  - Simulated latency (50-200ms).
  - Partial fill modeling based on L2 order book depth.
