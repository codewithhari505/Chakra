"""
Database Seeder Script — Phase 2 Implementation.

Initializes the database schema and performs high-speed bulk ingestion
of synthetic transaction and account records into the database.

Usage:
    python scripts/seed_database.py [--load-data] [--drop-existing] [--limit-txns 50000]
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import insert

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DatabaseSeeder")


async def seed(load_data: bool = False, drop_existing: bool = False, limit_txns: Optional[int] = None) -> None:
    from app.database.database import engine
    from app.database.init_db import init_db, drop_all_tables

    if drop_existing:
        logger.warning("Dropping all existing database tables...")
        await drop_all_tables()

    logger.info("Initializing database schema...")
    await init_db()

    if load_data:
        await load_synthetic_data(limit_txns=limit_txns)

    await engine.dispose()


async def load_synthetic_data(limit_txns: Optional[int] = None) -> None:
    from app.database.database import AsyncSessionLocal
    from app.models.account import Account
    from app.models.transaction import Transaction

    synthetic_dir = ROOT / "ml" / "data" / "synthetic"
    txn_path = synthetic_dir / "transactions.csv"
    acc_path = synthetic_dir / "accounts.csv"

    if not txn_path.exists() or not acc_path.exists():
        logger.error("Synthetic datasets not found! Run scripts/generate_data.py first.")
        return

    # 1. Accounts Bulk Load
    logger.info("Reading accounts from %s...", acc_path)
    accounts_df = pd.read_csv(acc_path)
    account_records = []
    for _, row in accounts_df.iterrows():
        reg_dt = None
        if pd.notna(row.get("registration_date")):
            reg_dt = datetime.fromisoformat(row["registration_date"]).replace(tzinfo=timezone.utc)
        account_records.append({
            "account_id": row["account_id"],
            "account_type": row["account_type"],
            "country": row.get("country", "India"),
            "city": row.get("city"),
            "registration_date": reg_dt,
            "is_flagged": bool(row.get("is_flagged", False)),
            "total_transactions": 0,
            "total_inflow": 0,
            "total_outflow": 0,
            "unique_senders": 0,
            "unique_receivers": 0,
            "degree": 0,
            "in_degree": 0,
            "out_degree": 0,
            "cycle_count": 0
        })

    logger.info("Bulk inserting %d accounts...", len(account_records))
    async with AsyncSessionLocal() as session:
        chunk_size = 2000
        for i in range(0, len(account_records), chunk_size):
            chunk = account_records[i : i + chunk_size]
            await session.execute(insert(Account), chunk)
        await session.commit()
    logger.info("Successfully loaded %d accounts into DB.", len(account_records))

    # 2. Transactions Bulk Load
    logger.info("Reading transactions from %s...", txn_path)
    txn_df = pd.read_csv(txn_path)
    if limit_txns:
        txn_df = txn_df.iloc[:limit_txns]
        logger.info("Capped transactions ingestion to %d rows.", limit_txns)

    total_rows = len(txn_df)
    batch_size = 5000
    total_inserted = 0

    logger.info("Bulk inserting %d transactions in batches of %d...", total_rows, batch_size)
    async with AsyncSessionLocal() as session:
        for start_idx in range(0, total_rows, batch_size):
            chunk = txn_df.iloc[start_idx : start_idx + batch_size]
            batch_data = []
            for _, r in chunk.iterrows():
                dt = datetime.fromisoformat(str(r["timestamp"])).replace(tzinfo=timezone.utc)
                batch_data.append({
                    "transaction_id": r["transaction_id"],
                    "sender_account_id": r["sender_account"],
                    "receiver_account_id": r["receiver_account"],
                    "amount": float(r["amount"]),
                    "currency": r.get("currency", "INR"),
                    "transaction_type": r["transaction_type"],
                    "timestamp": dt,
                    "location": r.get("location"),
                    "channel": r.get("channel"),
                    "device_id": r.get("device_id"),
                    "merchant_category": r.get("merchant_category"),
                    "is_suspicious": bool(r.get("is_suspicious", False)),
                    "detected_patterns": r.get("pattern_type")
                })
            await session.execute(insert(Transaction), batch_data)
            await session.commit()
            total_inserted += len(batch_data)
            logger.info("  -> Progress: %d / %d transactions committed.", total_inserted, total_rows)

    logger.info("Completed database loading: %d transactions seeded.", total_inserted)


def main():
    parser = argparse.ArgumentParser(description="Database initialization and seeding tool.")
    parser.add_argument("--load-data", action="store_true", help="Ingest synthetic data into database")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing tables before seeding")
    parser.add_argument("--limit-txns", type=int, default=None, help="Limit number of txns to load")
    args = parser.parse_args()

    asyncio.run(seed(load_data=args.load_data, drop_existing=args.drop_existing, limit_txns=args.limit_txns))


if __name__ == "__main__":
    main()
