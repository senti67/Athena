# ATHENA Developer Setup & Workflow Guide

## Prerequisites
* Python 3.11+
* Node.js 20+
* Docker & Docker Compose

---

## Local Setup Workflow
```bash
# 1. Install Python packages in editable mode
pip install -e .

# 2. Run automated tests
pytest tests/ -v

# 3. Run autonomous simulation
python scripts/run_simulation.py

# 4. Run event-driven backtester
python scripts/run_backtest.py

# 5. Start API Server
uvicorn apps.api.main:app --reload --port 8000

# 6. Start Next.js Web Dashboard
cd apps/web && npm run dev
```
