"""
Analytics API routes — dashboard summary data.

Endpoints:
  GET /analytics/overview             - KPI summary cards
  GET /analytics/risk-distribution    - Risk level breakdown
  GET /analytics/transaction-volume   - Volume over time (placeholder)
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.alert import Alert
from app.models.transaction import Transaction
from app.models.account import Account

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", summary="Dashboard KPI overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """
    Return high-level KPIs for the investigator dashboard:
    - Total transactions
    - Suspicious transactions
    - High-risk accounts
    - Open investigations
    """
    total_txns = (await db.execute(select(func.count()).select_from(Transaction))).scalar_one()
    suspicious_txns = (
        await db.execute(
            select(func.count()).select_from(Transaction).where(Transaction.is_suspicious == True)
        )
    ).scalar_one()
    high_risk_accounts = (
        await db.execute(
            select(func.count()).select_from(Account).where(
                Account.risk_level.in_(["HIGH", "CRITICAL"])
            )
        )
    ).scalar_one()
    open_investigations = (
        await db.execute(
            select(func.count()).select_from(Alert).where(
                Alert.status.in_(["NEW", "UNDER_REVIEW", "ESCALATED"])
            )
        )
    ).scalar_one()

    return {
        "total_transactions": total_txns,
        "suspicious_transactions": suspicious_txns,
        "high_risk_accounts": high_risk_accounts,
        "open_investigations": open_investigations,
        "suspicion_rate": round(suspicious_txns / total_txns * 100, 2) if total_txns > 0 else 0.0,
    }


@router.get("/risk-distribution", summary="Risk level distribution")
async def get_risk_distribution(db: AsyncSession = Depends(get_db)):
    """Return count of transactions/accounts per risk level."""
    txn_dist = (
        await db.execute(
            select(Transaction.risk_level, func.count().label("count"))
            .where(Transaction.risk_level.isnot(None))
            .group_by(Transaction.risk_level)
        )
    ).all()

    account_dist = (
        await db.execute(
            select(Account.risk_level, func.count().label("count"))
            .where(Account.risk_level.isnot(None))
            .group_by(Account.risk_level)
        )
    ).all()

    return {
        "transactions": {row.risk_level: row.count for row in txn_dist},
        "accounts": {row.risk_level: row.count for row in account_dist},
    }


@router.get("/transaction-network", summary="Transaction network data (stub)")
async def get_transaction_network():
    """
    Return graph data for network visualization.
    Full implementation in Phase 9 (Graph Analysis).
    """
    return {
        "status": "pending",
        "message": "Graph analysis will be available after Phase 9 implementation.",
        "nodes": [],
        "edges": [],
    }
