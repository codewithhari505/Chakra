"""
Unit tests for Phase 10: Unified Risk Scoring Engine.
"""

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.app.services.risk_engine import (
    UnifiedRiskScoringEngine,
    evaluate_transaction_risk,
)


@pytest.fixture
def risk_engine():
    return UnifiedRiskScoringEngine()


def test_unified_risk_score_calculation(risk_engine):
    sample_tx = {
        "transaction_id": "TX_UNIT_TEST",
        "amount": 96500.0,
        "transaction_amount": 96500.0,
        "hour": 14,
        "transaction_count_24h": 3,
        "location": "Mumbai",
        "device_id": "DEV9999",
    }
    report = risk_engine.calculate_risk(sample_tx, network_score=20.0)

    assert report.transaction_id == "TX_UNIT_TEST"
    assert 0.0 <= report.final_risk_score <= 100.0
    assert report.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "ml" in report.weights_used
    assert "rules" in report.weights_used
    assert len(report.triggered_rules) >= 1
    assert "Composite Risk Score:" in report.explanation_summary


def test_extreme_illicit_transaction_scores_high(risk_engine):
    illicit_tx = {
        "transaction_id": "TX_CRITICAL",
        "amount": 8_500_000.0,
        "transaction_amount": 8_500_000.0,
        "hour": 2,  # Night
        "transaction_count_1h": 5,
        "transaction_count_24h": 10,
        "location": "Zurich",  # High risk cross-border
        "has_overseas_certified_kyc": False,
        "device_id": "DEV_ANOM_001",
    }
    report = risk_engine.calculate_risk(illicit_tx, network_score=85.0)

    assert report.final_risk_score >= 60.0
    assert report.risk_level in ("HIGH", "CRITICAL")


def test_convenience_evaluate_transaction_risk():
    sample_tx = {"transaction_id": "TX_CONV", "amount": 500.0}
    report = evaluate_transaction_risk(sample_tx)
    assert report.final_risk_score >= 0.0
    d = report.to_dict()
    assert "component_scores" in d
    assert "final_risk_score" in d
