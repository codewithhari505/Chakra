"""
Unsupervised Anomaly Detection — Isolation Forest — Phase 8.

Detects novel, zero-day, and unlabeled suspicious patterns in financial transactions
by isolating outliers in high-dimensional behavioral feature space.

Outputs:
  - Raw decision function score (continuous outlier measure)
  - Normalized anomaly score scaled from 0 (completely normal) to 100 (extreme anomaly)
  - Binary anomaly flag (-1 for outlier, 1 for inlier per scikit-learn standard)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from ml.evaluation.metrics import EvaluationMetrics, compute_metrics
from ml.models.model_utils import load_model_artifact, save_model_artifact
from ml.models.supervised_model import AML_FEATURE_COLUMNS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AnomalyModel")


class AMLIsolationForestModel:
    """
    Isolation Forest model for unsupervised financial transaction anomaly detection.
    """

    def __init__(
        self,
        n_estimators: int = 150,
        max_samples: Union[int, float, str] = "auto",
        contamination: float = 0.05,
        random_state: int = 42,
        n_jobs: int = -1,
    ):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.random_state = random_state
        self.n_jobs = n_jobs

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )
        self.feature_names: List[str] = AML_FEATURE_COLUMNS
        self.is_fitted: bool = False

        # Min and max calibration anchors for 0-100 normalization
        self.score_min_: float = -0.5
        self.score_max_: float = 0.2

    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        cols = feature_cols or self.feature_names
        X = df[cols].fillna(0.0).values
        y = None
        if "is_suspicious" in df.columns:
            y = df["is_suspicious"].astype(int).values
        return X, y

    def fit(self, df_train: pd.DataFrame, normal_only: bool = True) -> "AMLIsolationForestModel":
        """
        Fits Isolation Forest.
        If normal_only=True and 'is_suspicious' is in df_train, trains on known normal traffic
        to maximize sensitivity to anomalies.
        """
        logger.info("Fitting Isolation Forest model on %d input records...", len(df_train))

        if normal_only and "is_suspicious" in df_train.columns:
            train_subset = df_train[df_train["is_suspicious"] == False]
            logger.info("Training on %d normal baseline records (normal_only=True)", len(train_subset))
        else:
            train_subset = df_train
            logger.info("Training on full unsupervised dataset of %d records", len(train_subset))

        X_train, _ = self.prepare_data(train_subset)
        self.model.fit(X_train)
        self.is_fitted = True

        # Calibrate decision function bounds on training data
        raw_scores = self.model.decision_function(X_train)
        self.score_min_ = float(np.percentile(raw_scores, 0.5))
        self.score_max_ = float(np.percentile(raw_scores, 99.5))
        logger.info("Isolation Forest fitted. Score range calibrated: [%.4f, %.4f]", self.score_min_, self.score_max_)
        return self

    def decision_function(self, df: pd.DataFrame) -> np.ndarray:
        """Raw decision function: lower scores indicate higher anomaly severity."""
        if not self.is_fitted:
            raise RuntimeError("Anomaly detector must be fitted before scoring.")
        X, _ = self.prepare_data(df)
        return self.model.decision_function(X)

    def predict_anomaly_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Converts decision function into a normalized 0 to 100 anomaly score:
          0   = Completely typical / conformant baseline
          100 = Severe structural anomaly
        """
        raw_scores = self.decision_function(df)
        # Decision function is higher for normal, lower for anomalous.
        # Invert so higher = more anomalous.
        span = self.score_max_ - self.score_min_
        if span <= 0:
            span = 1.0

        normalized = (self.score_max_ - raw_scores) / span
        scores_100 = np.clip(normalized * 100.0, 0.0, 100.0)
        return np.round(scores_100, 1)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Returns 1 for anomalies, 0 for inliers (inverted from scikit-learn standard for clarity)."""
        if not self.is_fitted:
            raise RuntimeError("Anomaly detector must be fitted before predict().")
        X, _ = self.prepare_data(df)
        raw_preds = self.model.predict(X)
        # raw_preds is 1 for inlier, -1 for outlier
        return (raw_preds == -1).astype(int)

    def evaluate(self, df_test: pd.DataFrame) -> EvaluationMetrics:
        """Evaluates anomaly detection against held-out ground-truth test partition."""
        if "is_suspicious" not in df_test.columns:
            raise ValueError("Evaluation DataFrame must contain 'is_suspicious' ground truth.")

        y_true = df_test["is_suspicious"].astype(int).values
        y_pred = self.predict(df_test)
        # Normalized anomaly probability/score in 0..1 for AUC calculation
        anomaly_scores = self.predict_anomaly_score(df_test) / 100.0

        metrics = compute_metrics(y_true, y_pred, anomaly_scores)
        logger.info(metrics.summary("Isolation Forest Anomaly Detector"))
        return metrics

    def save(
        self,
        filepath: Union[str, Path],
        metadata_path: Optional[Union[str, Path]] = None,
        metrics: Optional[EvaluationMetrics] = None
    ) -> None:
        meta_update = {
            "anomaly_detector": {
                "type": "IsolationForest",
                "status": "trained",
                "n_estimators": self.n_estimators,
                "contamination": self.contamination,
                "calibration_bounds": [self.score_min_, self.score_max_],
                "metrics": metrics.to_dict() if metrics else None,
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
    def load(cls, filepath: Union[str, Path]) -> "AMLIsolationForestModel":
        return load_model_artifact(filepath)
