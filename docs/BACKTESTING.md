# ATHENA Event-Driven Backtesting & Monte Carlo Engine

## Zero Look-Ahead Bias Guarantee
ATHENA's event-driven backtesting engine processes bars sequentially. Feature generation and regime detection only access point-in-time data available at or before bar timestamp `t`.

---

## Performance & Tail Risk Metrics
* **CAGR** (Compound Annual Growth Rate)
* **Sharpe Ratio** (Annualized excess return per unit of total risk)
* **Sortino Ratio** (Downside semi-variance risk-adjusted return)
* **Calmar Ratio** (CAGR / Maximum Drawdown)
* **Maximum Drawdown** (% peak-to-trough decline)
* **Win Rate & Profit Factor**
* **1-Day 95% Historical VaR & CVaR** (Expected Shortfall)

---

## Monte Carlo Forward Path Simulation
Executes 1,000 randomized bootstrap iterations of daily returns over a 252-day forward horizon to compute probability of ruin, median CAGR, and 95th percentile worst-case drawdown.
