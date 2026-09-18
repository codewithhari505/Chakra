"""
Database connection and session management.

Uses SQLAlchemy 2.0 async engine.
Supports both PostgreSQL (production) and SQLite (local development)
via the DATABASE_URL environment variable.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """
    Shared declarative base class for all SQLAlchemy ORM models.
    Import this in each model file and subclass it.
    """
    pass


def _create_engine() -> AsyncEngine:
    """
    Create the async database engine.
    
    SQLite: Uses check_same_thread=False for compatibility with async.
    PostgreSQL: Uses a connection pool sized for API workloads.
    """
    url = settings.database_url

    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=settings.debug,
        )

    # PostgreSQL / asyncpg
    return create_async_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,   # Detect stale connections before use
        echo=settings.debug,
    )


engine: AsyncEngine = _create_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Objects stay usable after commit
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """
    FastAPI dependency that yields a database session.
    
    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    
    The session is automatically closed after the request completes,
    and rolled back on any exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """
    Ping the database to verify connectivity.
    Used by the health-check endpoint.
    """
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
