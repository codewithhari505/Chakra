"""
Database initialization module.

Creates all tables defined in ORM models.
Run once during deployment or local setup — idempotent (won't drop existing tables).
"""

import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from app.database.database import Base, engine

# Import all models so that Base.metadata knows about them
# (Even if not directly used here, the import registers the table metadata)
import app.models.transaction  # noqa: F401
import app.models.account      # noqa: F401
import app.models.alert        # noqa: F401

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Create all database tables if they do not already exist.
    
    This function is called on application startup.
    For production, use Alembic migrations instead.
    """
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")


async def drop_all_tables() -> None:
    """
    Drop ALL tables. Use only in testing / development.
    NEVER call this in production.
    """
    logger.warning("Dropping all database tables — development only!")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
