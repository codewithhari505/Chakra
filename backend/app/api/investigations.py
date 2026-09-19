"""
Investigation Workflow API Routes — Phase 12 & 15.

Provides dedicated investigation management endpoints:
  GET  /investigations/summary                - Caseload metrics across all investigation states
  POST /investigations/assign                 - Assign alert to investigator (NEW -> UNDER_REVIEW)
  POST /investigations/escalate               - Escalate alert to full investigation (UNDER_REVIEW -> ESCALATED)
  POST /investigations/close                  - Close case with formal regulatory resolution
  POST /investigations/str                    - Generate formal FIU-IND STR reporting dossier
  POST /investigations/edd                    - Generate RBI 2026 EDD compliance docket
  GET  /investigations/{alert_id}/audit-trail - Fetch complete immutable audit log
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse
from app.services.investigation_service import (
    InvestigationService,
    InvestigationWorkflowError,
    VALID_RESOLUTIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/investigations", tags=["Investigations"])


class AssignRequest(BaseModel):
    alert_id: str
    assigned_investigator: str = Field(..., description="Officer or team assigned to case")
    notes: Optional[str] = Field(None, description="Initial triage notes")


class EscalateRequest(BaseModel):
    alert_id: str
    assigned_investigator: str = Field(..., description="Officer or team assigned to case")
    escalation_reason: str = Field(..., description="Reason for escalation")


class CloseCaseRequest(BaseModel):
    alert_id: str
    resolution: str = Field(..., description="TRUE_POSITIVE | FALSE_POSITIVE | SAR_FILED | STR_FILED")
    investigation_notes: str = Field(..., description="Investigator conclusion notes")
    officer_name: Optional[str] = Field("COMPLIANCE_OFFICER", description="Sign-off officer name")


class GenerateSTRRequest(BaseModel):
    alert_id: str
    officer_name: str = Field(..., description="Reporting officer name")
    narrative: Optional[str] = Field(None, description="Detailed grounds of suspicion narrative")


class GenerateEDDRequest(BaseModel):
    account_id: str
    risk_level: Optional[str] = Field("HIGH", description="Risk tier of the subject account")
    typology: Optional[str] = Field(None, description="Suspected pattern typology")


@router.get("/summary", summary="Get investigation caseload summary")
async def get_investigation_summary(db: AsyncSession = Depends(get_db)):
    """Returns real-time caseload metrics across all investigation states."""
    status_counts = (
        await db.execute(
            select(Alert.status, func.count().label("count"))
            .group_by(Alert.status)
        )
    ).all()

    counts = {s: 0 for s in ["NEW", "UNDER_REVIEW", "ESCALATED", "CLOSED"]}
    for row in status_counts:
        counts[row.status] = row.count

    return {
        "active_cases": counts["UNDER_REVIEW"] + counts["ESCALATED"],
        "pending_triage": counts["NEW"],
        "escalated_cases": counts["ESCALATED"],
        "closed_cases": counts["CLOSED"],
        "caseload_breakdown": counts,
    }


@router.post("/assign", response_model=AlertResponse, summary="Assign alert to investigator")
async def assign_alert(payload: AssignRequest, db: AsyncSession = Depends(get_db)):
    """Transitions alert from NEW -> UNDER_REVIEW."""
    result = await db.execute(select(Alert).where(Alert.alert_id == payload.alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{payload.alert_id}' not found.")

    try:
        InvestigationService.validate_transition(alert.status, "UNDER_REVIEW")
    except InvestigationWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    prev_status = alert.status
    alert.status = "UNDER_REVIEW"
    alert.assigned_to = payload.assigned_investigator
    alert.reviewed_at = datetime.now(tz=timezone.utc)
    if payload.notes:
        alert.investigation_notes = payload.notes

    InvestigationService.log_audit_event(
        alert_id=alert.alert_id,
        action="ASSIGN_CASE",
        actor=payload.assigned_investigator,
        previous_status=prev_status,
        new_status="UNDER_REVIEW",
        notes=payload.notes,
    )

    await db.flush()
    await db.refresh(alert)
    return alert


@router.post("/escalate", response_model=AlertResponse, summary="Escalate alert to active investigation")
async def escalate_alert(payload: EscalateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.alert_id == payload.alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{payload.alert_id}' not found.")

    prev_status = alert.status
    alert.status = "ESCALATED"
    alert.assigned_to = payload.assigned_investigator
    alert.investigation_notes = f"Escalated: {payload.escalation_reason}"

    InvestigationService.log_audit_event(
        alert_id=alert.alert_id,
        action="ESCALATE_ALERT",
        actor=payload.assigned_investigator,
        previous_status=prev_status,
        new_status="ESCALATED",
        notes=payload.escalation_reason,
    )

    await db.flush()
    await db.refresh(alert)
    return alert


@router.post("/close", response_model=AlertResponse, summary="Close investigation case")
async def close_case(payload: CloseCaseRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.alert_id == payload.alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{payload.alert_id}' not found.")

    prev_status = alert.status
    alert.status = "CLOSED"
    alert.resolution = payload.resolution
    alert.investigation_notes = payload.investigation_notes
    alert.closed_at = datetime.now(tz=timezone.utc)

    InvestigationService.log_audit_event(
        alert_id=alert.alert_id,
        action="CLOSE_CASE",
        actor=payload.officer_name or alert.assigned_to or "COMPLIANCE_OFFICER",
        previous_status=prev_status,
        new_status="CLOSED",
        notes=f"Resolution: {payload.resolution} | {payload.investigation_notes}",
    )

    await db.flush()
    await db.refresh(alert)
    return alert


@router.post("/str", summary="Generate formal FIU-IND Suspicious Transaction Report (STR)")
async def generate_fiu_str(payload: GenerateSTRRequest, db: AsyncSession = Depends(get_db)):
    """
    Generates a formal FIU-IND Suspicious Transaction Report compliant with
    PMLA 2002 §12 and PML Rules 2005.
    """
    result = await db.execute(select(Alert).where(Alert.alert_id == payload.alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{payload.alert_id}' not found.")

    alert_dict = {
        "alert_id": alert.alert_id,
        "account_id": alert.account_id,
        "transaction_id": alert.transaction_id,
        "risk_score": alert.risk_score,
        "risk_level": alert.risk_level,
        "alert_type": alert.alert_type,
        "explanation": alert.explanation,
        "assigned_to": alert.assigned_to,
    }

    str_dossier = InvestigationService.generate_fiu_str_payload(
        alert_dict=alert_dict,
        investigator_officer=payload.officer_name,
        narrative=payload.narrative,
    )

    InvestigationService.log_audit_event(
        alert_id=alert.alert_id,
        action="GENERATE_FIU_STR",
        actor=payload.officer_name,
        previous_status=alert.status,
        new_status=alert.status,
        notes="Generated formal FIU-IND Suspicious Transaction Report under PMLA §12.",
    )

    return {
        "status": "success",
        "dossier": str_dossier,
    }


@router.post("/edd", summary="Generate RBI 2026 Enhanced Due Diligence (EDD) Docket")
async def generate_rbi_edd(payload: GenerateEDDRequest):
    """
    Generates an Enhanced Due Diligence compliance checklist conforming to
    the RBI 2026 Know Your Customer Amendment Directions.
    """
    docket = InvestigationService.generate_rbi_edd_docket(
        account_id=payload.account_id,
        risk_level=payload.risk_level or "HIGH",
        suspected_typology=payload.typology,
    )
    return {
        "status": "success",
        "docket": docket,
    }


@router.get("/{alert_id}/audit-trail", summary="Get audit trail history for an alert")
async def get_case_audit_trail(alert_id: str):
    """Retrieves immutable audit history for regulatory examination."""
    trail = InvestigationService.get_audit_trail(alert_id)
    return {
        "alert_id": alert_id,
        "total_events": len(trail),
        "events": trail,
    }
