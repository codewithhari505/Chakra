"""
Model Training Runner — Phase 6, 7 & 8.

Orchestrates supervised model training (Random Forest & XGBoost) and
unsupervised anomaly detection (Isolation Forest) on engineered features,
computes evaluation metrics on held-out temporal test set, logs feature importances,
and registers artifacts in models/v1/metadata.json.

Usage:
    python scripts/train_models.py [--model rf|xgb|isolation|all] [--seed 42]
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.models.supervised_model import AMLRandomForestModel, AMLXGBoostModel
from ml.models.anomaly_model import AMLIsolationForestModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TrainModels")


def train_random_forest(
    train_path: Path,
    test_path: Path,
    output_model_path: Path,
    metadata_path: Path,
    seed: int = 42,
) -> None:
    logger.info("=== Phase 6: Training Random Forest AML Classifier ===")
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    rf_model = AMLRandomForestModel(
        n_estimators=150,
        max_depth=16,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight="balanced_subsample",
        random_state=seed,
    )
    rf_model.fit(train_df)
    metrics = rf_model.evaluate(test_df)

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    rf_model.save(filepath=output_model_path, metadata_path=metadata_path, metrics=metrics)
    logger.info("Random Forest trained and saved successfully.")


def train_xgboost(
    train_path: Path,
    test_path: Path,
    output_model_path: Path,
    metadata_path: Path,
    seed: int = 42,
) -> None:
    logger.info("=== Phase 7: Training XGBoost AML Classifier ===")
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    xgb_model = AMLXGBoostModel(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=seed,
    )
    xgb_model.fit(train_df)
    metrics = xgb_model.evaluate(test_df)

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    xgb_model.save(filepath=output_model_path, metadata_path=metadata_path, metrics=metrics)
    logger.info("XGBoost trained and saved successfully.")


def train_isolation_forest(
    train_path: Path,
    test_path: Path,
    output_model_path: Path,
    metadata_path: Path,
    seed: int = 42,
) -> None:
    logger.info("=== Phase 8: Training Isolation Forest Anomaly Detector ===")
    logger.info("Loading training data: %s", train_path)
    train_df = pd.read_csv(train_path)

    logger.info("Loading test data: %s", test_path)
    test_df = pd.read_csv(test_path)

    # Contamination set to ~7% to match realistic illicit transaction proportion
    iso_model = AMLIsolationForestModel(
        n_estimators=150,
        contamination=0.07,
        random_state=seed,
    )
    iso_model.fit(train_df, normal_only=True)

    logger.info("Evaluating Isolation Forest on held-out temporal test set...")
    metrics = iso_model.evaluate(test_df)

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    iso_model.save(filepath=output_model_path, metadata_path=metadata_path, metrics=metrics)
    logger.info("Isolation Forest trained and saved successfully.")


def main():
    parser = argparse.ArgumentParser(description="Train AML detection models.")
    parser.add_argument(
        "--model",
        choices=["rf", "xgb", "isolation", "all"],
        default="isolation",
        help="Which model to train",
    )
    parser.add_argument(
        "--train",
        type=str,
        default=str(ROOT / "ml" / "data" / "processed" / "train_features.csv"),
    )
    parser.add_argument(
        "--test",
        type=str,
        default=str(ROOT / "ml" / "data" / "processed" / "test_features.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(ROOT / "models" / "v1"),
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    model_dir = Path(args.output_dir)
    rf_path = model_dir / "fraud_classifier.pkl"
    xgb_path = model_dir / "xgboost_classifier.pkl"
    iso_path = model_dir / "anomaly_detector.pkl"
    meta_path = model_dir / "metadata.json"

    if args.model in ("rf", "all"):
        train_random_forest(
            train_path=Path(args.train),
            test_path=Path(args.test),
            output_model_path=rf_path,
            metadata_path=meta_path,
            seed=args.seed,
        )
    if args.model in ("xgb", "all"):
        train_xgboost(
            train_path=Path(args.train),
            test_path=Path(args.test),
            output_model_path=xgb_path,
            metadata_path=meta_path,
            seed=args.seed,
        )
    if args.model in ("isolation", "all"):
        train_isolation_forest(
            train_path=Path(args.train),
            test_path=Path(args.test),
            output_model_path=iso_path,
            metadata_path=meta_path,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
