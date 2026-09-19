"""
Phase 16: Full End-to-End System Integration Tests.

Validates the continuous flow across the entire AML system:
1. Transaction Ingestion & Preprocessing
2. Unified 4-Pillar Risk Engine Scoring (XGBoost + Isolation Forest + PMLA Rules + NetworkX)
3. Inference Latency (< 50ms UPI switch budget check)
4. Dynamic Alert Generation
5. Investigation Caseload Lifecycle (NEW -> UNDER_REVIEW -> ESCALATED -> CLOSED)
6. Regulatory Compliance Reporting (FIU-IND STR Filing & RBI 2026 EDD Docket)
7. Complete Immutable Audit Trail Verification
"""

import os
import sys
import time
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_aml.db"

from app.main import app
from app.services.risk_engine import evaluate_transaction_risk
from app.services.investigation_service import InvestigationService

client = TestClient(app)


def test_e2e_normal_transaction_lifecycle():
    """Verify that legitimate day-to-day transactions score LOW risk and incur no unnecessary regulatory burden."""
    normal_txn = {
        "transaction_id": "TXN_E2E_NORM_001",
        "sender_account_id": "ACC_CONSUMER_10",
        "receiver_account_id": "ACC_MERCHANT_20",
        "amount": 2450.0,
        "currency": "INR",
        "transaction_type": "PAYMENT",
        "timestamp": "2026-09-19T10:15:00",
        "channel": "UPI",
        "location": "Bengaluru",
        "is_suspicious": False,
    }

    # Warm up client to exclude initial Python module / SQLite schema initialization latency
    client.post(
        "/api/v1/transactions/analyze",
        json={"transaction": normal_txn, "include_graph": False, "include_explanation": False},
    )

    # Measure warm in-memory API response latency
    t0 = time.perf_counter()
    response = client.post(
        "/api/v1/transactions/analyze",
        json={
            "transaction": normal_txn,
            "include_graph": False,
            "include_explanation": True,
        },
    )
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000.0

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    analysis = data["analysis"]
    # Verify low risk classification
    assert analysis["risk_level"] in ["LOW", "MEDIUM"]
    assert analysis["final_risk_score"] < 50.0
    # Strict latency constraint for in-line test client HTTP roundtrip (< 150ms)
    assert latency_ms < 150.0, f"Inline latency exceeded budget: {latency_ms:.2f}ms"


def test_e2e_illicit_structuring_to_str_filing_pipeline():
    """
    Simulates end-to-end detection of a ₹98,000 structuring attempt
    through model scoring, rule violation, triage, and formal FIU-IND STR generation.
    """
    structuring_txn = {
        "transaction_id": "TXN_E2E_STRUC_98K",
        "sender_account_id": "ACC_SUSPECT_01",
        "receiver_account_id": "ACC_MULE_02",
        "amount": 98000.0,
        "transaction_amount": 98000.0,
        "currency": "INR",
        "transaction_type": "TRANSFER",
        "timestamp": "2026-09-19T02:30:00",  # Off-hours
        "hour": 2,
        "transaction_count_1h": 4,
        "transaction_count_24h": 8,
        "channel": "UPI",
        "location": "Mumbai",
        "device_id": "DEV_UNVERIFIED_99",
        "is_suspicious": True,
    }

    # Stage 1: Ingestion & 4-Pillar Risk Engine Scoring
    t0 = time.perf_counter()
    eval_res = evaluate_transaction_risk(structuring_txn, network_score=75.0)
    eval_time = (time.perf_counter() - t0) * 1000.0

    assert eval_time < 50.0, f"Unified risk scoring must be < 50ms (took {eval_time:.2f}ms)"
    assert eval_res.final_risk_score >= 30.0  # Elevated risk
    assert eval_res.risk_level in ["MEDIUM", "HIGH", "CRITICAL"]

    # Verify statutory structuring rule fired
    rule_ids = [r.get("rule_id", "") if isinstance(r, dict) else str(r) for r in eval_res.triggered_rules]
    assert any("R001" in r or "STRUCTURING" in r for r in rule_ids)

    # Stage 2: Investigation Case Creation & Triage Lifecycle
    alert_id = "ALT_E2E_STRUC_001"

    # Action 1: Assign to Investigator (NEW -> UNDER_REVIEW)
    InvestigationService.validate_transition("NEW", "UNDER_REVIEW")
    InvestigationService.log_audit_event(
        alert_id=alert_id,
        action="ASSIGN_CASE",
        actor="OFFICER_PATEL",
        previous_status="NEW",
        new_status="UNDER_REVIEW",
        notes="High probability structuring flag (₹98,000 via UPI off-hours).",
    )

    # Action 2: Escalate Case (UNDER_REVIEW -> ESCALATED)
    InvestigationService.validate_transition("UNDER_REVIEW", "ESCALATED")
    InvestigationService.log_audit_event(
        alert_id=alert_id,
        action="ESCALATE_ALERT",
        actor="OFFICER_PATEL",
        previous_status="UNDER_REVIEW",
        new_status="ESCALATED",
        notes="Confirmed deliberate structuring under PMLA 2002 §35A.",
    )

    # Stage 3: Regulatory Compliance Dossier Generation
    # Sub-task A: FIU-IND Suspicious Transaction Report
    mock_alert_dict = {
        "alert_id": alert_id,
        "account_id": structuring_txn["sender_account_id"],
        "transaction_id": structuring_txn["transaction_id"],
        "risk_score": eval_res.final_risk_score,
        "risk_level": eval_res.risk_level,
        "alert_type": "STRUCTURING",
        "assigned_to": "OFFICER_PATEL",
    }
    str_payload = InvestigationService.generate_fiu_str_payload(
        alert_dict=mock_alert_dict,
        transaction_dict=structuring_txn,
        investigator_officer="OFFICER_PATEL",
        narrative="Structured transfer of ₹98,000 at 02:30 AM intended to evade statutory ₹1,00,000 threshold.",
    )
    assert str_payload["header"]["report_type"] == "STR_PMLA_2002_SEC12"
    assert str_payload["subject_entity"]["reported_transaction_amount_inr"] == 98000.0
    assert str_payload["suspicion_profile"]["flagged_typology"] == "STRUCTURING"

    # Sub-task B: RBI 2026 Enhanced Due Diligence (EDD) Docket
    edd_docket = InvestigationService.generate_rbi_edd_docket(
        account_id=structuring_txn["sender_account_id"],
        risk_level=eval_res.risk_level,
        suspected_typology="STRUCTURING",
    )
    assert "RBI Master Direction - KYC Amendment Directions 2026" in edd_docket["statutory_framework"]
    assert len(edd_docket["statutory_requirements"]) >= 4

    # Stage 4: Formal Resolution & Close Case (ESCALATED -> CLOSED)
    InvestigationService.validate_transition("ESCALATED", "CLOSED")
    InvestigationService.log_audit_event(
        alert_id=alert_id,
        action="CLOSE_CASE",
        actor="OFFICER_PATEL",
        previous_status="ESCALATED",
        new_status="CLOSED",
        notes="STR filed with FIU-IND; EDD pack transmitted to branch for account freeze.",
        metadata={"resolution": "STR_FILED"},
    )

    # Stage 5: Immutable Audit Trail Verification
    audit_trail = InvestigationService.get_audit_trail(alert_id)
    assert len(audit_trail) == 3
    statuses = [(e["previous_status"], e["new_status"]) for e in audit_trail]
    assert statuses == [
        ("NEW", "UNDER_REVIEW"),
        ("UNDER_REVIEW", "ESCALATED"),
        ("ESCALATED", "CLOSED"),
    ]
