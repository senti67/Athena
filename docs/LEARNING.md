# ATHENA Offline Bayesian Learning & Calibration

## Closed-Loop Offline Learning
To prevent dangerous live self-modification loops, ATHENA runs learning cycles **strictly offline**.
Weight updates and model re-calibrations generate formal proposals with status `PENDING_OPERATOR_APPROVAL`.

---

## 1. Bayesian Reliability Updating
Dynamically adjusts agent weights (Technical, Quant, Fundamental, Sentiment, Macro, Microstructure) according to historical accuracy and prevailing market regime.

## 2. Platt Scaling & Probability Calibration
Calibrates raw model confidence scores into true empirical probabilities using Platt logistic scaling and monitors Brier scores and Expected Calibration Error (ECE).
