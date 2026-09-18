"""
Model Training Runner — Phase 6.

Orchestrates supervised model training (Random Forest) on engineered features,
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

from ml.models.supervised_model import AMLRandomForestModel

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
    logger.info("Loading training data: %s", train_path)
    train_df = pd.read_csv(train_path)

    logger.info("Loading test data: %s", test_path)
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

    logger.info("Evaluating on held-out temporal test set...")
    metrics = rf_model.evaluate(test_df)

    logger.info("Top Contributing Features (Split Importances):")
    for feat in rf_model.get_feature_importances(10):
        logger.info("  %2d. %-25s : %.4f", feat["rank"], feat["feature"], feat["importance"])

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    rf_model.save(filepath=output_model_path, metadata_path=metadata_path, metrics=metrics)
    logger.info("Random Forest trained and saved successfully.")


def train_xgboost():
    """Phase 7: Train XGBoost classifier."""
    logger.info("[PHASE 7] XGBoost training — planned for Phase 7.")


def train_isolation_forest():
    """Phase 8: Train Isolation Forest anomaly detector."""
    logger.info("[PHASE 8] Isolation Forest training — planned for Phase 8.")


def main():
    parser = argparse.ArgumentParser(description="Train AML detection models.")
    parser.add_argument(
        "--model",
        choices=["rf", "xgb", "isolation", "all"],
        default="rf",
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
        train_xgboost()
    if args.model in ("isolation", "all"):
        train_isolation_forest()


if __name__ == "__main__":
    main()
