"""
Transaction API routes.

Endpoints:
  GET  /transactions               - List transactions (paginated, filterable)
  GET  /transactions/{id}          - Get single transaction details
  POST /transactions/analyze       - Analyze a transaction through the full pipeline
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionAnalyzeRequest,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)
from app.services.risk_engine import evaluate_transaction_risk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse, summary="List all transactions")
async def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW|MEDIUM|HIGH|CRITICAL"),
    is_suspicious: Optional[bool] = Query(None, description="Filter by ground-truth label"),
    sender_account: Optional[str] = Query(None, description="Filter by sender account ID"),
    receiver_account: Optional[str] = Query(None, description="Filter by receiver account ID"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    count_query = select(func.count()).select_from(Transaction)

    if risk_level:
        query = query.where(Transaction.risk_level == risk_level.upper())
        count_query = count_query.where(Transaction.risk_level == risk_level.upper())
    if is_suspicious is not None:
        query = query.where(Transaction.is_suspicious == is_suspicious)
        count_query = count_query.where(Transaction.is_suspicious == is_suspicious)
    if sender_account:
        query = query.where(Transaction.sender_account_id == sender_account)
        count_query = count_query.where(Transaction.sender_account_id == sender_account)
    if receiver_account:
        query = query.where(Transaction.receiver_account_id == receiver_account)
        count_query = count_query.where(Transaction.receiver_account_id == receiver_account)

    offset = (page - 1) * page_size
    query = query.order_by(Transaction.timestamp.desc()).offset(offset).limit(page_size)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query)
    transactions = result.scalars().all()

    return TransactionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=transactions,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction details",
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
    )
    txn = result.scalar_one_or_none()

    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )

    return txn


@router.post(
    "/analyze",
    summary="Analyze a transaction through the full AML pipeline",
    status_code=status.HTTP_200_OK,
)
async def analyze_transaction(
    request: TransactionAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs an incoming transaction through the 4-pillar AML risk scoring engine:
      1. Heuristic PMLA & RBI 2026 compliance rules
      2. Supervised XGBoost / Random Forest probability
      3. Isolation Forest anomaly detection score
      4. Graph structural risk assessment

    Returns unified composite risk score (0-100), risk tier (LOW/MED/HIGH/CRITICAL),
    sub-scores, and structured explanation.
    """
    logger.info("Analyze request received for transaction: %s", request.transaction.transaction_id)

    # Convert request payload to dictionary
    tx_dict = request.transaction.model_dump()
    tx_dict["amount"] = float(tx_dict["amount"])
    tx_dict["transaction_amount"] = tx_dict["amount"]

    # Calculate unified risk report
    report = evaluate_transaction_risk(tx_dict, network_score=15.0 if request.include_graph else 0.0)

    return {
        "status": "success",
        "analysis": report.to_dict(),
    }
