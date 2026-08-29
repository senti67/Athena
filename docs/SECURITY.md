# ATHENA Security, Cryptography & RBAC Guide

## 1. Authentication & RBAC
- Signed JWT access tokens (HS256) with refresh token rotation.
- Role-based permissions:
  - `ADMIN`: Full platform configuration and live switches.
  - `TRADER`: Order execution, portfolio management, and paper/live trading.
  - `RESEARCHER`: Backtesting, feature exploration, and model calibration.
  - `VIEWER`: Read-only access to dashboard and trade reports.

## 2. Zero Credential Leakage
- Structured JSON logging engine automatically redacts secrets, tokens, and API keys.
- Broker API secrets are never returned to client endpoints.
