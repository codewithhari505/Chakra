"""
Unit tests for Phase 12: Complete FastAPI Route Suite.
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


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_investigations_summary_endpoint(client):
    r = client.get("/api/v1/investigations/summary")
    assert r.status_code == 200
    data = r.json()
    assert "active_cases" in data
    assert "caseload_breakdown" in data
    assert "pending_triage" in data


def test_transaction_network_endpoint(client):
    r = client.get("/api/v1/analytics/transaction-network?limit_nodes=20")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)


def test_analyze_endpoint_returns_composite_risk(client):
    payload = {
        "transaction": {
            "transaction_id": "TX_TEST_PHASE12",
            "sender_account_id": "ACC_SND_99",
            "receiver_account_id": "ACC_RCV_99",
            "amount": 94500.0,
            "currency": "INR",
            "transaction_type": "TRANSFER",
            "timestamp": "2025-07-01T12:00:00Z",
            "location": "Mumbai",
            "channel": "ONLINE",
            "device_id": "DEV999",
            "merchant_category": "FINANCIAL",
            "is_suspicious": False,
        },
        "include_graph": True,
        "include_explanation": True,
    }
    r = client.post("/api/v1/transactions/analyze", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "success"
    analysis = res["analysis"]
    assert analysis["transaction_id"] == "TX_TEST_PHASE12"
    assert 0.0 <= analysis["final_risk_score"] <= 100.0
    assert analysis["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "component_scores" in analysis
    assert "ml_score" in analysis["component_scores"]
    assert "rule_score" in analysis["component_scores"]
    assert "network_score" in analysis["component_scores"]
