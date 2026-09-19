"""
Analytics API routes — dashboard summary data & network graph inspection.

Endpoints:
  GET /analytics/overview             - KPI summary cards
  GET /analytics/risk-distribution    - Risk level breakdown
  GET /analytics/transaction-network  - Subgraph network topology for graph visualization
  GET /analytics/patterns             - Detected cycles, layering chains, and dispersion hubs
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
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


@router.get("/transaction-network", summary="Transaction network graph visualization data")
async def get_transaction_network(
    account_id: Optional[str] = Query(None, description="Center graph around specific account"),
    limit_nodes: int = Query(50, ge=5, le=200, description="Max node count for visualization"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns graph topology (nodes and edges) formatted for React Flow / Cytoscape / VisJS visualization.
    """
    # Fetch recent or suspect transactions to form visualization graph
    query = select(Transaction)
    if account_id:
        query = query.where(
            (Transaction.sender_account_id == account_id) |
            (Transaction.receiver_account_id == account_id)
        )
    else:
        # Default: prioritize suspicious transactions for investigator review
        query = query.where(Transaction.is_suspicious == True)

    query = query.order_by(Transaction.timestamp.desc()).limit(limit_nodes * 2)
    txns = (await db.execute(query)).scalars().all()

    nodes_dict = {}
    edges = []

    for tx in txns:
        snd = tx.sender_account_id
        rcv = tx.receiver_account_id
        if not snd or not rcv:
            continue

        if snd not in nodes_dict:
            nodes_dict[snd] = {
                "id": snd,
                "label": snd,
                "is_suspicious": tx.is_suspicious,
                "risk_level": "HIGH" if tx.is_suspicious else "LOW",
            }
        if rcv not in nodes_dict:
            nodes_dict[rcv] = {
                "id": rcv,
                "label": rcv,
                "is_suspicious": tx.is_suspicious,
                "risk_level": "HIGH" if tx.is_suspicious else "LOW",
            }

        edges.append({
            "id": tx.transaction_id,
            "source": snd,
            "target": rcv,
            "amount": float(tx.amount),
            "timestamp": str(tx.timestamp),
            "is_suspicious": tx.is_suspicious,
            "pattern": tx.detected_patterns or "NORMAL",
        })

        if len(nodes_dict) >= limit_nodes:
            break

    return {
        "status": "success",
        "nodes_count": len(nodes_dict),
        "edges_count": len(edges),
        "nodes": list(nodes_dict.values()),
        "edges": edges,
    }
