# ATHENA Trade Explainability Engine

Every executed trade automatically records an end-to-end audit snapshot generating an institutional Markdown Trade Report:
- **Symbol & Action**: e.g., BUY AAPL
- **Ensemble Confidence & Calibrated Probability**: e.g., 82% (75% Platt)
- **Market Regime**: Detected state (BULL, BEAR, SIDEWAYS, VOLATILE)
- **Supporting vs Opposing Agents**: Full list of votes and points
- **Alternative Scenarios & Hedging Triggers**: Macro rates spike, earnings multiples contraction
- **Risk Assessment & Veto Clearance**: Proof of adherence to exposure, drawdown, and size limits
- **Execution Fills & Slippage**: Actual fill price, slippage in bps, and fees.
