"""
ATHENA Database Seeding Script
"""

import asyncio
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.database.session import init_db
from packages.logging.logger import get_logger
from services.data_service.pipeline import data_pipeline

logger = get_logger("athena.seed")


async def main():
    logger.info("Initializing ATHENA database tables...")
    await init_db()

    symbols = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "SPY", "QQQ", "TLT", "GLD", "BTC"]
    logger.info(f"Seeding historical market data for {len(symbols)} universe symbols...")

    for sym in symbols:
        candles = await data_pipeline.ingest_candles(sym, limit=200)
        logger.info(f"Seeded {len(candles)} bars for {sym} (Latest Close: ${candles[-1].close:.2f})")

    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
