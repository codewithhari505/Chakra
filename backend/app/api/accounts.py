"""
Account API routes.

Endpoints:
  GET /accounts                        - List accounts (paginated, filterable)
  GET /accounts/{account_id}           - Get account profile
  GET /accounts/{account_id}/transactions - Get transactions for an account
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountListResponse, AccountResponse
from app.schemas.transaction import TransactionListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=AccountListResponse, summary="List all accounts")
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    is_flagged: Optional[bool] = Query(None, description="Filter flagged accounts only"),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated, filterable list of accounts."""
    query = select(Account)
    count_query = select(func.count()).select_from(Account)

    if risk_level:
        query = query.where(Account.risk_level == risk_level.upper())
        count_query = count_query.where(Account.risk_level == risk_level.upper())
    if is_flagged is not None:
        query = query.where(Account.is_flagged == is_flagged)
        count_query = count_query.where(Account.is_flagged == is_flagged)

    offset = (page - 1) * page_size
    query = query.order_by(Account.risk_score.desc().nullslast()).offset(offset).limit(page_size)

    total = (await db.execute(count_query)).scalar_one()
    accounts = (await db.execute(query)).scalars().all()

    return AccountListResponse(total=total, page=page, page_size=page_size, items=accounts)


@router.get("/{account_id}", response_model=AccountResponse, summary="Get account profile")
async def get_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """Return full profile for a single account."""
    result = await db.execute(select(Account).where(Account.account_id == account_id))
    account = result.scalar_one_or_none()

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found.",
        )
    return account


@router.get(
    "/{account_id}/transactions",
    response_model=TransactionListResponse,
    summary="Get transactions for an account",
)
async def get_account_transactions(
    account_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Return all transactions where the account appears as sender or receiver."""
    query = select(Transaction).where(
        or_(
            Transaction.sender_account_id == account_id,
            Transaction.receiver_account_id == account_id,
        )
    )
    count_query = select(func.count()).select_from(Transaction).where(
        or_(
            Transaction.sender_account_id == account_id,
            Transaction.receiver_account_id == account_id,
        )
    )

    offset = (page - 1) * page_size
    query = query.order_by(Transaction.timestamp.desc()).offset(offset).limit(page_size)

    total = (await db.execute(count_query)).scalar_one()
    transactions = (await db.execute(query)).scalars().all()

    return TransactionListResponse(total=total, page=page, page_size=page_size, items=transactions)
