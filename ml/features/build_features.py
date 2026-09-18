"""
Feature Pipeline Runner — Phase 4.

Combines transaction-level features and account behavioral features into
a unified modeling dataset for both training and test partitions.

Usage:
    python ml/features/build_features.py
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from ml.features.transaction_features import extract_transaction_features
from ml.features.behavioral_features import extract_behavioral_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("BuildFeatures")


def generate_feature_set(
    df: pd.DataFrame,
    accounts_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """Extracts and merges all transaction and behavioral features for a dataset."""
    logger.info("Generating feature set for %d transactions...", len(df))

    # 1. Transaction features
    txn_feats = extract_transaction_features(df)

    # 2. Behavioral features
    behav_feats = extract_behavioral_features(df, accounts_df=accounts_df)

    # 3. Merge on transaction_id
    merged = df.merge(txn_feats, on="transaction_id", how="left")
    merged = merged.merge(behav_feats, on="transaction_id", how="left")

    logger.info("Successfully assembled %d total columns (metadata + features + labels).", merged.shape[1])
    return merged


def run_feature_pipeline(
    train_path: Path,
    test_path: Path,
    accounts_path: Path,
    output_dir: Path
) -> None:
    logger.info("Reading train, test, and accounts datasets...")
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    accounts_df = pd.read_csv(accounts_path) if accounts_path.exists() else None

    # Compute features for training partition
    logger.info("Processing Training Partition...")
    train_featured = generate_feature_set(train_df, accounts_df=accounts_df)

    # Compute features for testing partition
    logger.info("Processing Testing Partition...")
    test_featured = generate_feature_set(test_df, accounts_df=accounts_df)

    output_dir.mkdir(parents=True, exist_ok=True)
    train_out = output_dir / "train_features.csv"
    test_out = output_dir / "test_features.csv"

    train_featured.to_csv(train_out, index=False)
    test_featured.to_csv(test_out, index=False)

    logger.info("Feature engineering complete!")
    logger.info("  Train Features: %s (%d rows, %d cols)", train_out, len(train_featured), train_featured.shape[1])
    logger.info("  Test Features : %s (%d rows, %d cols)", test_out, len(test_featured), test_featured.shape[1])


def main():
    parser = argparse.ArgumentParser(description="Extract transaction & behavioral features.")
    parser.add_argument(
        "--train",
        type=str,
        default=str(ROOT / "ml" / "data" / "processed" / "train.csv"),
    )
    parser.add_argument(
        "--test",
        type=str,
        default=str(ROOT / "ml" / "data" / "processed" / "test.csv"),
    )
    parser.add_argument(
        "--accounts",
        type=str,
        default=str(ROOT / "ml" / "data" / "synthetic" / "accounts.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(ROOT / "ml" / "data" / "processed"),
    )
    args = parser.parse_args()

    run_feature_pipeline(
        train_path=Path(args.train),
        test_path=Path(args.test),
        accounts_path=Path(args.accounts),
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
