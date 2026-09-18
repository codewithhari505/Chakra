"""
Unit tests for Phase 5: Rule-Based AML Detection Engine & RBI 2026 KYC Integration.
"""

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.rules.rule_engine import AMLRuleEngine
from backend.app.services.risk_engine import evaluate_transaction_rules


@pytest.fixture
def rule_engine():
    return AMLRuleEngine()


def test_normal_transaction_triggers_no_rules(rule_engine):
    normal_tx = {
        "amount": 2500.0,
        "hour": 14,
        "transaction_count_1h": 0,
        "transaction_count_24h": 0,
        "amount_deviation": 1.0,
        "inflow_outflow_ratio": 1.0,
        "location": "Mumbai",
        "device_id": "DEV1234"
    }
    evaluation = rule_engine.evaluate_transaction(normal_tx)

    assert evaluation.rule_score == 0.0
    assert evaluation.triggered_count == 0
    assert len(evaluation.triggered_rules) == 0
    assert "conforms to normal" in evaluation.summary_explanation.lower()


def test_high_value_and_critical_rule(rule_engine):
    # INR 1.5 million -> High value (not critical)
    tx_high = {"amount": 1_500_000.0, "hour": 11}
    eval_high = rule_engine.evaluate_transaction(tx_high)
    rule_ids = [r.rule_id for r in eval_high.triggered_rules]
    assert "RULE_HIGH_VALUE" in rule_ids
    assert eval_high.rule_score >= 30.0

    # INR 6 million -> Critical value
    tx_crit = {"amount": 6_000_000.0, "hour": 11}
    eval_crit = rule_engine.evaluate_transaction(tx_crit)
    crit_rule_ids = [r.rule_id for r in eval_crit.triggered_rules]
    assert "RULE_CRITICAL_HIGH_VALUE" in crit_rule_ids
    assert eval_crit.rule_score >= 45.0


def test_structuring_pmla_rule(rule_engine):
    # Structuring: INR 96,500 with 3 transactions in 24h
    tx_struct = {
        "amount": 96_500.0,
        "transaction_count_24h": 3,
        "hour": 15
    }
    evaluation = rule_engine.evaluate_transaction(tx_struct)
    rule_ids = [r.rule_id for r in evaluation.triggered_rules]

    assert "RULE_STRUCTURING_PMLA" in rule_ids
    struct_rule = [r for r in evaluation.triggered_rules if r.rule_id == "RULE_STRUCTURING_PMLA"][0]
    assert struct_rule.severity == "CRITICAL"
    assert "INR 100,000 threshold" in struct_rule.reason


def test_rapid_velocity_rule(rule_engine):
    tx_velocity = {
        "amount": 5000.0,
        "transaction_count_1h": 4,  # >= 3 in 1 hour
        "hour": 12
    }
    evaluation = rule_engine.evaluate_transaction(tx_velocity)
    rule_ids = [r.rule_id for r in evaluation.triggered_rules]
    assert "RULE_RAPID_VELOCITY_1H" in rule_ids


def test_off_hours_high_value_rule(rule_engine):
    tx_night = {
        "amount": 350_000.0,  # > 200k
        "hour": 2,            # 02:00 AM (night window)
    }
    evaluation = rule_engine.evaluate_transaction(tx_night)
    rule_ids = [r.rule_id for r in evaluation.triggered_rules]
    assert "RULE_OFF_HOURS_HIGH_VALUE" in rule_ids


def test_rbi_2026_kyc_cross_border_rule(rule_engine):
    # Cross border to Dubai without certified overseas KYC
    tx_cross = {
        "amount": 50_000.0,
        "location": "Dubai",
        "has_overseas_certified_kyc": False
    }
    evaluation = rule_engine.evaluate_transaction(tx_cross)
    rule_ids = [r.rule_id for r in evaluation.triggered_rules]
    assert "RULE_RBI_2026_KYC_CROSS_BORDER" in rule_ids
    assert any("RBI (Commercial Banks" in ref for r in evaluation.triggered_rules for ref in r.regulatory_references)


def test_backend_service_integration():
    sample_payload = {
        "amount": 95000.0,
        "transaction_count_24h": 4,
        "hour": 23,  # night + structuring
        "location": "Zurich",
        "has_overseas_certified_kyc": False
    }
    eval_res = evaluate_transaction_rules(sample_payload)
    assert eval_res.rule_score > 60.0
    assert eval_res.triggered_count >= 2
    d = eval_res.to_dict()
    assert "rule_score" in d
    assert "triggered_rules" in d
