"""
Unit tests for Phase 11: Explainable AI & SHAP Local Attributions.
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.models.supervised_model import AMLXGBoostModel, AML_FEATURE_COLUMNS
from ml.explainability.shap_explainer import AMLTransactionExplainer, FeatureContribution


@pytest.fixture
def trained_xgb_model():
    rng = np.random.default_rng(42)
    n = 200
    data = {col: rng.normal(10, 2, size=n) for col in AML_FEATURE_COLUMNS}
    data["amount"] = rng.uniform(100, 50000, size=n)
    data["is_suspicious"] = rng.choice([0, 1], size=n, p=[0.9, 0.1])
    df = pd.DataFrame(data)

    model = AMLXGBoostModel(n_estimators=10, max_depth=3, random_state=42)
    model.fit(df)
    return model


def test_shap_explainer_initialization_and_attribution(trained_xgb_model):
    explainer = AMLTransactionExplainer(model=trained_xgb_model)
    sample_tx = {
        "transaction_amount": 75000.0,
        "log_transaction_amount": 11.2,
        "transaction_count_24h": 5.0,
        "outflow_amount_24h": 300000.0,
    }

    exps = explainer.explain_transaction(sample_tx, top_n=4)

    assert len(exps) == 4
    for item in exps:
        assert isinstance(item, FeatureContribution)
        assert item.impact_direction in ("INCREASES_RISK", "DECREASES_RISK")
        assert "feature" in item.to_dict()
        assert "contribution" in item.to_dict()


def test_heuristic_fallback_when_model_is_none():
    explainer = AMLTransactionExplainer(model=None)
    sample_tx = {"transaction_amount": 5000.0}
    exps = explainer.explain_transaction(sample_tx, top_n=3)

    assert len(exps) == 3
    assert all(isinstance(e, FeatureContribution) for e in exps)
