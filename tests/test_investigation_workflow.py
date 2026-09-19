"""
Unit tests for Investigation Workflow Service — Phase 15.
Tests state machine transitions, FIU-IND STR generation, and RBI 2026 EDD compliance dockets.
"""

import os
import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_aml.db"

from app.main import app
from app.services.investigation_service import (
    InvestigationService,
    InvestigationWorkflowError,
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_valid_state_transitions():
    """Verify standard investigation lifecycle transitions."""
    assert InvestigationService.validate_transition("NEW", "UNDER_REVIEW") is True
    assert InvestigationService.validate_transition("UNDER_REVIEW", "ESCALATED") is True
    assert InvestigationService.validate_transition("ESCALATED", "CLOSED") is True
    assert InvestigationService.validate_transition("UNDER_REVIEW", "CLOSED") is True
    assert InvestigationService.validate_transition("CLOSED", "UNDER_REVIEW", is_supervisor=True) is True


def test_invalid_state_transitions():
    """Verify illegal transitions throw InvestigationWorkflowError."""
    # Cannot close directly from NEW without review
    with pytest.raises(InvestigationWorkflowError):
        InvestigationService.validate_transition("NEW", "CLOSED")

    # Cannot jump from NEW to ESCALATED without triage
    with pytest.raises(InvestigationWorkflowError):
        InvestigationService.validate_transition("NEW", "ESCALATED")

    # Non-supervisor cannot reopen closed case
    with pytest.raises(InvestigationWorkflowError):
        InvestigationService.validate_transition("CLOSED", "UNDER_REVIEW", is_supervisor=False)


def test_generate_fiu_str_payload():
    """Verify generated STR payload strictly aligns with PMLA 2002 §12 standards."""
    mock_alert = {
        "alert_id": "ALT_MOCK_001",
        "account_id": "ACC_TEST_99",
        "transaction_id": "TXN_TEST_44",
        "risk_score": 88.5,
        "risk_level": "CRITICAL",
        "alert_type": "CIRCULAR_TRANSFER",
        "assigned_to": "OFFICER_SHARMA",
    }
    mock_txn = {
        "amount": 250000.0,
        "channel": "UPI",
        "timestamp": "2026-09-19T05:00:00Z",
        "sender_account_id": "ACC_TEST_99",
        "receiver_account_id": "ACC_TEST_100",
    }

    str_dossier = InvestigationService.generate_fiu_str_payload(
        alert_dict=mock_alert,
        transaction_dict=mock_txn,
        investigator_officer="OFFICER_SHARMA",
        narrative="Directed circular funds flow detected across 4 hops.",
    )

    assert str_dossier["header"]["report_type"] == "STR_PMLA_2002_SEC12"
    assert "FIU-IND" in str_dossier["header"]["regulatory_authority"]
    assert str_dossier["subject_entity"]["account_id"] == "ACC_TEST_99"
    assert str_dossier["subject_entity"]["reported_transaction_amount_inr"] == 250000.0
    assert str_dossier["suspicion_profile"]["composite_risk_score"] == 88.5
    assert str_dossier["suspicion_profile"]["flagged_typology"] == "CIRCULAR_TRANSFER"
    assert "not a judicial finding of guilt" in str_dossier["investigation_sign_off"]["disclaimer"]


def test_generate_rbi_edd_docket():
    """Verify EDD docket enforces RBI 2026 KYC Amendment Directions."""
    docket = InvestigationService.generate_rbi_edd_docket(
        account_id="ACC_CROSSBORDER_01",
        risk_level="CRITICAL",
        suspected_typology="CROSS_BORDER_REMITTANCE",
    )

    assert docket["account_id"] == "ACC_CROSSBORDER_01"
    assert "RBI Master Direction - KYC Amendment Directions 2026" in docket["statutory_framework"]
    reqs = docket["statutory_requirements"]
    assert len(reqs) >= 4

    req_text = " ".join(r["requirement"] for r in reqs)
    # Check 10% UBO rule
    assert "10%" in req_text
    # Check overseas 6 authorized bodies
    assert "Indian Embassy" in req_text
    assert "foreign public notaries" in req_text


def test_audit_trail_recording():
    """Verify immutable audit events are recorded and queryable."""
    InvestigationService.log_audit_event(
        alert_id="ALT_AUDIT_TEST",
        action="ASSIGN_CASE",
        actor="INSPECTOR_RAO",
        previous_status="NEW",
        new_status="UNDER_REVIEW",
        notes="Starting deep forensic triage",
    )

    trail = InvestigationService.get_audit_trail("ALT_AUDIT_TEST")
    assert len(trail) >= 1
    assert trail[-1]["action"] == "ASSIGN_CASE"
    assert trail[-1]["actor"] == "INSPECTOR_RAO"
    assert trail[-1]["previous_status"] == "NEW"
    assert trail[-1]["new_status"] == "UNDER_REVIEW"


def test_api_edd_endpoint(client):
    """Verify POST /api/v1/investigations/edd endpoint returns 200 and valid schema."""
    response = client.post(
        "/api/v1/investigations/edd",
        json={"account_id": "ACC_TEST_888", "risk_level": "HIGH", "typology": "STRUCTURING"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "docket" in data
    assert data["docket"]["account_id"] == "ACC_TEST_888"
