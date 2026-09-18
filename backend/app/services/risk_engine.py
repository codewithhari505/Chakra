"""
Risk Scoring Engine Service — Integrates Rule-Based AML Detection and Composite Risk Calculation.

Phase 5: Rule-Based Detection integration (PMLA statutory limits, RBI 2026 KYC Directions,
velocity, structuring, off-hours, and cybersecurity device signals).
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.rules.rule_engine import AMLRuleEngine, RuleEvaluation, RuleResult

_rule_engine_instance: Optional[AMLRuleEngine] = None


def get_rule_engine() -> AMLRuleEngine:
    """Returns singleton instance of AMLRuleEngine."""
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = AMLRuleEngine()
    return _rule_engine_instance


def evaluate_transaction_rules(transaction_data: Dict[str, Any]) -> RuleEvaluation:
    """Convenience helper to evaluate rule engine against transaction payload."""
    engine = get_rule_engine()
    return engine.evaluate_transaction(transaction_data)
