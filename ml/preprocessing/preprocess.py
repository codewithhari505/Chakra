"""
Reusable Preprocessing Pipeline — Phase 3.

Implements leak-free feature preprocessing:
  1. Temporal train/test splitting (train on past, test on future)
  2. Numerical transformations (log1p transform, robust/standard scaling)
  3. Categorical encoding with unseen category tolerance
  4. Model artifact persistence (saving/loading preprocessor via joblib)

Adheres strictly to zero data leakage:
- Preprocessor statistics (means, medians, categories) are fit ONLY on train.
- Exact same pipeline transforms test and real-time inference transactions.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, RobustScaler

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from ml.preprocessing.clean_data import TransactionCleaner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Preprocessor")


def temporal_train_test_split(
    df: pd.DataFrame,
    test_ratio: float = 0.2,
    timestamp_col: str = "timestamp"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits transaction data strictly chronologically to prevent temporal data leakage.
    Earliest records become train; latest records become test.
    """
    df_sorted = df.sort_values(by=timestamp_col).reset_index(drop=True)
    split_idx = int(len(df_sorted) * (1.0 - test_ratio))
    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()

    logger.info(
        "Temporal Split: Train=%d rows (%s to %s) | Test=%d rows (%s to %s)",
        len(train_df),
        train_df[timestamp_col].min(),
        train_df[timestamp_col].max(),
        len(test_df),
        test_df[timestamp_col].min(),
        test_df[timestamp_col].max(),
    )
    return train_df, test_df


class DataPreprocessor(BaseEstimator, TransformerMixin):
    """
    End-to-end data preprocessor for AML transaction models.
    """

    CATEGORICAL_FEATURES = [
        "transaction_type",
        "channel",
        "merchant_category",
        "currency"
    ]

    NUMERICAL_FEATURES = [
        "amount",
        "log_amount",
        "hour",
        "day_of_week",
        "day_of_month",
        "is_weekend"
    ]

    def __init__(self):
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.scaler = RobustScaler()
        self.feature_names_: List[str] = []
        self.is_fitted: bool = False

    def _extract_base_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts deterministic temporal and mathematical features."""
        df_feat = df.copy()

        # Timestamp features
        if not pd.api.types.is_datetime64_any_dtype(df_feat["timestamp"]):
            df_feat["timestamp"] = pd.to_datetime(df_feat["timestamp"])

        df_feat["hour"] = df_feat["timestamp"].dt.hour
        df_feat["day_of_week"] = df_feat["timestamp"].dt.dayofweek
        df_feat["day_of_month"] = df_feat["timestamp"].dt.day
        df_feat["is_weekend"] = df_feat["day_of_week"].isin([5, 6]).astype(int)

        # Log transform of amount to handle heavy-tailed monetary distribution
        amounts = np.clip(pd.to_numeric(df_feat["amount"], errors="coerce").fillna(0.0), a_min=0.0, a_max=None)
        df_feat["log_amount"] = np.log1p(amounts)

        # Clean string categories
        for col in self.CATEGORICAL_FEATURES:
            if col in df_feat.columns:
                df_feat[col] = df_feat[col].astype(str).str.strip().str.upper()
            else:
                df_feat[col] = "UNKNOWN"

        return df_feat

    def fit(self, X: pd.DataFrame, y=None) -> "DataPreprocessor":
        """
        Fits encoder on categorical fields and scaler on numerical fields.
        Fit is executed exclusively on training data.
        """
        df_feat = self._extract_base_features(X)

        # Fit categorical encoder
        cat_data = df_feat[self.CATEGORICAL_FEATURES]
        self.encoder.fit(cat_data)
        encoded_cat_names = list(self.encoder.get_feature_names_out(self.CATEGORICAL_FEATURES))

        # Fit numerical scaler
        num_data = df_feat[self.NUMERICAL_FEATURES]
        self.scaler.fit(num_data)

        self.feature_names_ = self.NUMERICAL_FEATURES + encoded_cat_names
        self.is_fitted = True

        logger.info("DataPreprocessor fitted successfully. Total output feature dimensions: %d", len(self.feature_names_))
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transforms input transactions into a normalized feature matrix.
        Unseen categorical levels are safely encoded as zeros.
        """
        if not self.is_fitted:
            raise RuntimeError("DataPreprocessor must be fitted before calling transform().")

        df_feat = self._extract_base_features(X)

        # Scale numerical features
        num_data = df_feat[self.NUMERICAL_FEATURES]
        scaled_num = self.scaler.transform(num_data)

        # Encode categorical features
        cat_data = df_feat[self.CATEGORICAL_FEATURES]
        encoded_cat = self.encoder.transform(cat_data)

        # Combine
        feature_matrix = np.hstack([scaled_num, encoded_cat])
        return feature_matrix

    def fit_transform(self, X: pd.DataFrame, y=None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def save(self, filepath: Union[str, Path]) -> None:
        """Saves fitted preprocessor state using joblib."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Saved preprocessor to %s", path)

    @staticmethod
    def load(filepath: Union[str, Path]) -> "DataPreprocessor":
        """Loads fitted preprocessor state."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Preprocessor artifact not found at {path}")
        preprocessor = joblib.load(path)
        logger.info("Loaded preprocessor from %s", path)
        return preprocessor


def run_preprocessing_pipeline(
    input_csv: Path,
    output_dir: Path,
    model_dir: Path,
    test_ratio: float = 0.2
) -> None:
    logger.info("Loading raw transaction data from %s...", input_csv)
    raw_df = pd.read_csv(input_csv)

    # 1. Clean data
    cleaner = TransactionCleaner()
    clean_df, audit_report = cleaner.clean(raw_df)

    # 2. Temporal Split
    train_df, test_df = temporal_train_test_split(clean_df, test_ratio=test_ratio)

    # 3. Fit preprocessor on train only
    preprocessor = DataPreprocessor()
    preprocessor.fit(train_df)

    # 4. Save preprocessor artifact
    model_dir.mkdir(parents=True, exist_ok=True)
    preprocessor_path = model_dir / "preprocessor.joblib"
    preprocessor.save(preprocessor_path)

    # Also save feature scaler specifically if requested by architecture
    scaler_path = model_dir / "feature_scaler.pkl"
    joblib.dump(preprocessor.scaler, scaler_path)

    # 5. Save cleaned train and test partitions
    output_dir.mkdir(parents=True, exist_ok=True)
    train_out = output_dir / "train.csv"
    test_out = output_dir / "test.csv"
    train_df.to_csv(train_out, index=False)
    test_df.to_csv(test_out, index=False)

    logger.info("Preprocessing complete:")
    logger.info("  Cleaned Train saved to : %s (%d rows)", train_out, len(train_df))
    logger.info("  Cleaned Test saved to  : %s (%d rows)", test_out, len(test_df))
    logger.info("  Preprocessor saved to  : %s", preprocessor_path)


def main():
    parser = argparse.ArgumentParser(description="Clean and preprocess transaction dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(ROOT / "ml" / "data" / "synthetic" / "transactions.csv"),
        help="Input synthetic/raw CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(ROOT / "ml" / "data" / "processed"),
        help="Directory to save train/test processed CSVs",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=str(ROOT / "models" / "v1"),
        help="Directory to save preprocessor artifact",
    )
    parser.add_argument("--test-ratio", type=float, default=0.2, help="Test split ratio (chronological)")
    args = parser.parse_args()

    run_preprocessing_pipeline(
        input_csv=Path(args.input),
        output_dir=Path(args.output_dir),
        model_dir=Path(args.model_dir),
        test_ratio=args.test_ratio,
    )


if __name__ == "__main__":
    main()
