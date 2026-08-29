.PHONY: help install test lint run-api run-alpaca docker-up docker-down seed simulate backtest

help:
	@echo "ATHENA Institutional Quantitative Platform Commands (Alpaca Integrated):"
	@echo "  make install      Install all python dependencies"
	@echo "  make test         Run all unit, integration, and failure tests"
	@echo "  make lint         Run ruff and black linter checks"
	@echo "  make run-api      Run FastAPI backend locally"
	@echo "  make run-alpaca   Run autonomous Alpaca Paper Trading cycle"
	@echo "  make docker-up    Start all containerized services"
	@echo "  make docker-down  Stop all containerized services"
	@echo "  make seed         Seed database with assets and historical market data"
	@echo "  make simulate     Run end-to-end multi-agent trading simulation"
	@echo "  make backtest     Run event-driven backtesting engine"

install:
	pip install -e .

test:
	pytest tests/ -v

lint:
	ruff check .
	black --check .

run-api:
	uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

run-alpaca:
	python scripts/run_alpaca_live.py AAPL

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

seed:
	python scripts/seed_data.py

simulate:
	python scripts/run_simulation.py

backtest:
	python scripts/run_backtest.py
