"""
ATHENA Database Engine & Async Session Factory
Supports PostgreSQL with TimescaleDB/pgvector and SQLite for zero-config local testing.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from packages.common.config import settings
from packages.logging.logger import get_logger

logger = get_logger("athena.database")

Base = declarative_base()

# Async Engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    future=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous Engine (for Alembic migrations and sync scripts)
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=settings.SQL_ECHO,
    future=True,
)

SyncSessionFactory = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async database session context manager with automatic rollback on error."""
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        raise
    finally:
        await session.close()


async def init_db():
    """Initializes database schema tables."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Database table initialization warning (may already exist): {str(e)}")
