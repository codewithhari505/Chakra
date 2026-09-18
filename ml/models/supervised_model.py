"""
Supervised ML Classifier — Random Forest & XGBoost — Phase 6 & 7.

Implements supervised models for financial transaction suspiciousness classification:
  - Input: Engineered transaction, temporal, and account behavioral features.
  - Class Imbalance Mitigation: Balanced class weights / sub-sampling.
  - Output: Continuous suspicion probability calibrated to 0–100 risk score.
  - Explainability: Top feature importances extracted from tree splits.

Adheres strictly to zero data leakage:
  - Model fits only on past training partition.
  - Evaluates on future held-out temporal partition.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from ml.evaluation.metrics import EvaluationMetrics, compute_metrics
from ml.models.model_utils import load_model_artifact, save_model_artifact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SupervisedModel")


# Standard modeling feature columns (excluding identifiers, targets, and leakage artifacts)
AML_FEATURE_COLUMNS = [
    "transaction_amount",
    "log_transaction_amount",
    "transaction_hour",
    "transaction_day",
    "transaction_day_of_week",
    "is_weekend",
    "is_night",
    "transaction_count_1h",
    "transaction_count_24h",
    "transaction_count_7d",
    "outflow_amount_24h",
    "inflow_amount_24h",
    "amount_deviation",
    "log_amount_deviation",
    "inflow_outflow_ratio",
    "account_age_days",
    "total_sender_txns",
    "cumulative_outflow",
    "sender_avg_txn_size",
    "sender_max_txn_size",
    "receiver_cumulative_inflow",
    "unique_receivers_count",
    "unique_senders_count",
    "transaction_velocity",
    "unusual_transaction_ratio",
]


class AMLRandomForestModel:
    """
    Random Forest Classifier optimized for rare AML transaction detection.
    """

    def __init__(
        self,
        n_estimators: int = 150,
        max_depth: int = 16,
        min_samples_split: int = 10,
        min_samples_leaf: int = 4,
        class_weight: str = "balanced_subsample",
        random_state: int = 42,
        n_jobs: int = -1,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.class_weight = class_weight
        self.random_state = random_state
        self.n_jobs = n_jobs

        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            class_weight=self.class_weight,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )
        self.feature_names: List[str] = AML_FEATURE_COLUMNS
        self.is_fitted: bool = False

    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Prepares numerical feature matrix X and ground truth y."""
        cols = feature_cols or self.feature_names
        X = df[cols].fillna(0.0).values

        y = None
        if "is_suspicious" in df.columns:
            y = df["is_suspicious"].astype(int).values

        return X, y

    def fit(self, df_train: pd.DataFrame) -> "AMLRandomForestModel":
        """Fits Random Forest classifier on training data."""
        logger.info("Fitting Random Forest classifier on %d training records...", len(df_train))
        X_train, y_train = self.prepare_data(df_train)

        if y_train is None:
            raise ValueError("Training DataFrame must contain 'is_suspicious' label column.")

        suspicious_count = int(y_train.sum())
        logger.info("Training Class Distribution: Suspicious=%d (%.2f%%) | Normal=%d",
                    suspicious_count, suspicious_count / len(y_train) * 100, len(y_train) - suspicious_count)

        self.model.fit(X_train, y_train)
        self.is_fitted = True
        logger.info("Random Forest model trained successfully.")
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Returns continuous suspicion probabilities for the positive class (range 0.0 to 1.0)."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba().")
        X, _ = self.prepare_data(df)
        return self.model.predict_proba(X)[:, 1]

    def predict(self, df: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Returns binary classification predictions based on decision threshold."""
        proba = self.predict_proba(df)
        return (proba >= threshold).astype(int)

    def predict_risk_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Converts probability into a normalized 0–100 risk score:
        Risk Score = Probability * 100
        """
        proba = self.predict_proba(df)
        return np.clip(np.round(proba * 100.0, 1), 0.0, 100.0)

    def evaluate(self, df_test: pd.DataFrame, threshold: float = 0.5) -> EvaluationMetrics:
        """Evaluates model performance against a test DataFrame."""
        if "is_suspicious" not in df_test.columns:
            raise ValueError("Evaluation DataFrame must contain 'is_suspicious' ground truth.")

        X_test, y_test = self.prepare_data(df_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= threshold).astype(int)

        metrics = compute_metrics(y_test, y_pred, y_prob)
        logger.info(metrics.summary("Random Forest"))
        return metrics

    def get_feature_importances(self, top_n: int = 15) -> List[Dict[str, Any]]:
        """Extracts top contributing features from the trained Random Forest."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before getting feature importances.")

        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]

        top_feats = []
        for i in range(min(top_n, len(self.feature_names))):
            idx = indices[i]
            top_feats.append({
                "feature": self.feature_names[idx],
                "importance": float(round(importances[idx], 4)),
                "rank": i + 1,
            })
        return top_feats

    def save(self, filepath: Union[str, Path], metadata_path: Optional[Union[str, Path]] = None, metrics: Optional[EvaluationMetrics] = None) -> None:
        """Serializes model artifact to disk."""
        meta_update = {
            "fraud_classifier": {
                "type": "RandomForest",
                "status": "trained",
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "metrics": metrics.to_dict() if metrics else None,
                "top_features": self.get_feature_importances(10),
            }
        }
        save_model_artifact(
            model=self,
            filepath=filepath,
            feature_names=self.feature_names,
            metadata_update=meta_update,
            metadata_json_path=metadata_path,
        )

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "AMLRandomForestModel":
        """Loads serialized model."""
        return load_model_artifact(filepath)
