# ATHENA Independent Risk Management & Safety Controls

## Unilateral Veto Power
The Risk Management Engine operates as an independent guardian. An AI agent or quantitative strategy may only propose orders; the Risk Engine validates every request and holds unilateral veto power.

---

## Hard Institutional Bounds

1. **Maximum Daily Loss**: $5,000.00 hard stop. When reached, trading is halted for the session.
2. **Maximum Position Size**: $50,000.00 (or 10% NAV).
3. **Maximum Portfolio Exposure**: 100% unleveraged.
4. **Maximum Drawdown Limit**: 15.0% trailing kill threshold.
5. **Data Quality Score**: Trading is blocked if `data_quality_score < 0.80`.
6. **Minimum Reward-to-Risk**: >= 1.5:1 required on all discretionary entries.
7. **Emergency Kill Switch**: Instant platform-wide freeze of all order placement.
