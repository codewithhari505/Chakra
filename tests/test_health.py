"""
Phase 1 & 2 Tests — Health check and basic API sanity using standard TestClient.

Run with:
    pytest tests/test_health.py -v
"""

import os
import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# Use local sqlite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_aml.db"

from app.main import app


@pytest.fixture(scope="module")
def client():
    # TestClient manages event loop and startup/shutdown lifespan automatically
    with TestClient(app) as c:
        yield c

    # Cleanup test db
    test_db = Path("./test_aml.db")
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AML" in data["message"]


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "models_loaded" in data
    assert data["status"] in ("healthy", "degraded")


def test_transactions_empty(client):
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_accounts_empty(client):
    response = client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_alerts_empty(client):
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_analytics_overview(client):
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "suspicious_transactions" in data
    assert "high_risk_accounts" in data
    assert "open_investigations" in data


def test_transaction_not_found(client):
    response = client.get("/api/v1/transactions/TX_DOES_NOT_EXIST")
    assert response.status_code == 404


def test_account_not_found(client):
    response = client.get("/api/v1/accounts/ACC_DOES_NOT_EXIST")
    assert response.status_code == 404
