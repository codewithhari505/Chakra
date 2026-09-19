"""
Unit tests for Phase 6, 7 & 8: Supervised ML Models (Random Forest & XGBoost) and Isolation Forest.
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.models.supervised_model import (
    AML_FEATURE_COLUMNS,
    AMLRandomForestModel,
    AMLXGBoostModel,
)
from ml.models.anomaly_model import AMLIsolationForestModel


@pytest.fixture
def synthetic_train_test_data():
    """Generates synthetic dataset for rapid model unit testing."""
    rng = np.random.default_rng(42)
    n_train = 300
    n_test = 100

    def make_df(n):
        data = {col: rng.normal(10, 2, size=n) for col in AML_FEATURE_COLUMNS}
        data["amount"] = rng.uniform(100, 50000, size=n)
        # 10% positive class
        data["is_suspicious"] = rng.choice([0, 1], size=n, p=[0.9, 0.1])
        return pd.DataFrame(data)

    return make_df(n_train), make_df(n_test)


def test_random_forest_fit_predict_and_risk_score(synthetic_train_test_data):
    df_train, df_test = synthetic_train_test_data
    rf = AMLRandomForestModel(n_estimators=10, max_depth=4, random_state=42)
    rf.fit(df_train)

    assert rf.is_fitted is True

    proba = rf.predict_proba(df_test)
    assert len(proba) == len(df_test)
    assert (proba >= 0.0).all() and (proba <= 1.0).all()

    risk_scores = rf.predict_risk_score(df_test)
    assert len(risk_scores) == len(df_test)
    assert (risk_scores >= 0.0).all() and (risk_scores <= 100.0).all()

    top_feats = rf.get_feature_importances(top_n=5)
    assert len(top_feats) == 5
    assert "feature" in top_feats[0]
    assert "importance" in top_feats[0]


def test_xgboost_fit_predict_and_risk_score(synthetic_train_test_data):
    df_train, df_test = synthetic_train_test_data
    xgb = AMLXGBoostModel(n_estimators=15, max_depth=3, random_state=42)
    xgb.fit(df_train)

    assert xgb.is_fitted is True

    proba = xgb.predict_proba(df_test)
    assert len(proba) == len(df_test)
    assert (proba >= 0.0).all() and (proba <= 1.0).all()

    metrics = xgb.evaluate(df_test)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.roc_auc <= 1.0
    assert metrics.confusion_mat is not None


def test_isolation_forest_fit_predict_and_anomaly_score(synthetic_train_test_data):
    df_train, df_test = synthetic_train_test_data
    iso = AMLIsolationForestModel(n_estimators=15, contamination=0.1, random_state=42)
    iso.fit(df_train)

    assert iso.is_fitted is True

    scores = iso.predict_anomaly_score(df_test)
    assert len(scores) == len(df_test)
    assert (scores >= 0.0).all() and (scores <= 100.0).all()

    preds = iso.predict(df_test)
    assert set(np.unique(preds)).issubset({0, 1})

    metrics = iso.evaluate(df_test)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.roc_auc <= 1.0


def test_model_serialization(tmp_path, synthetic_train_test_data):
    df_train, df_test = synthetic_train_test_data
    xgb = AMLXGBoostModel(n_estimators=10, max_depth=3, random_state=42)
    xgb.fit(df_train)

    save_path = tmp_path / "test_xgb.pkl"
    xgb.save(save_path)
    assert save_path.exists()

    loaded = AMLXGBoostModel.load(save_path)
    assert loaded.is_fitted is True

    orig_preds = xgb.predict_proba(df_test)
    loaded_preds = loaded.predict_proba(df_test)
    np.testing.assert_allclose(orig_preds, loaded_preds, rtol=1e-5)
