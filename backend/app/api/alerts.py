"""
Alert API routes.

Endpoints:
  GET   /alerts                - List alerts (paginated, filterable by status/risk)
  GET   /alerts/{alert_id}     - Get alert details
  PATCH /alerts/{alert_id}     - Update alert during investigation
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertListResponse, AlertResponse, AlertUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse, summary="List all alerts")
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status", description="NEW|UNDER_REVIEW|ESCALATED|CLOSED"),
    risk_level: Optional[str] = Query(None, description="LOW|MEDIUM|HIGH|CRITICAL"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated, filterable list of AML alerts."""
    query = select(Alert)
    count_query = select(func.count()).select_from(Alert)

    if status_filter:
        query = query.where(Alert.status == status_filter.upper())
        count_query = count_query.where(Alert.status == status_filter.upper())
    if risk_level:
        query = query.where(Alert.risk_level == risk_level.upper())
        count_query = count_query.where(Alert.risk_level == risk_level.upper())
    if alert_type:
        query = query.where(Alert.alert_type == alert_type.upper())
        count_query = count_query.where(Alert.alert_type == alert_type.upper())

    offset = (page - 1) * page_size
    query = query.order_by(Alert.created_at.desc()).offset(offset).limit(page_size)

    total = (await db.execute(count_query)).scalar_one()
    alerts = (await db.execute(query)).scalars().all()

    return AlertListResponse(total=total, page=page, page_size=page_size, items=alerts)


@router.get("/{alert_id}", response_model=AlertResponse, summary="Get alert details")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Return full details for a single alert, including investigation notes."""
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse, summary="Update alert (investigation workflow)")
async def update_alert(
    alert_id: str,
    update: AlertUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an alert during the investigation process.
    
    Investigators can:
    - Change status (NEW → UNDER_REVIEW → ESCALATED / CLOSED)
    - Assign to an investigator
    - Add investigation notes
    - Record resolution
    """
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )

    now = datetime.now(tz=timezone.utc)

    if update.status:
        prev_status = alert.status
        alert.status = update.status

        # Track timestamps for workflow events
        if update.status == "UNDER_REVIEW" and prev_status == "NEW":
            alert.reviewed_at = now
        elif update.status == "CLOSED":
            alert.closed_at = now

    if update.assigned_to is not None:
        alert.assigned_to = update.assigned_to
    if update.investigation_notes is not None:
        alert.investigation_notes = update.investigation_notes
    if update.resolution is not None:
        alert.resolution = update.resolution

    await db.flush()
    await db.refresh(alert)
    return alert
