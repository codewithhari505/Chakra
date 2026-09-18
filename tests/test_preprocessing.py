"""
Unit tests for Phase 3: Data Cleaning and Preprocessing Pipeline.
"""

import tempfile
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.preprocessing.clean_data import TransactionCleaner, CleaningReport
from ml.preprocessing.preprocess import DataPreprocessor, temporal_train_test_split


@pytest.fixture
def dirty_transaction_data():
    """Provides a synthetic dirty DataFrame with known anomalies."""
    return pd.DataFrame({
        "transaction_id": ["TX01", "TX02", "TX02", "TX03", "TX04", "TX05", "TX06", "TX07"],
        "sender_account": ["ACC1", "ACC2", "ACC2", None, "ACC3", "ACC4", "ACC5", "ACC6"],
        "receiver_account": ["ACC2", "ACC3", "ACC3", "ACC4", None, "ACC4", "ACC7", "ACC8"], # TX05 is self-transfer
        "amount": [1000.0, 5000.0, 5000.0, 200.0, 300.0, 400.0, -50.0, 0.0],                # TX06 and TX07 have invalid amounts
        "timestamp": [
            "2025-01-01 10:00:00",
            "2025-01-01 11:00:00",
            "2025-01-01 11:00:00", # Duplicate
            "2025-01-01 12:00:00", # Missing sender
            "2025-01-01 13:00:00", # Missing receiver
            "2025-01-01 14:00:00", # Self-transfer
            "2025-01-01 15:00:00", # Negative amount
            "2025-01-01 16:00:00", # Zero amount
        ],
        "channel": ["ONLINE", "MOBILE", "MOBILE", "BRANCH", None, "ATM", "ONLINE", "BRANCH"],
        "location": ["Mumbai", None, None, "Delhi", "Chennai", "Kolkata", "Pune", "Jaipur"],
        "merchant_category": ["FINANCIAL", "RETAIL", "RETAIL", "FOOD", "TRAVEL", "UTILITIES", "HEALTHCARE", "ENTERTAINMENT"],
        "transaction_type": ["TRANSFER", "PAYMENT", "PAYMENT", "TRANSFER", "TRANSFER", "TRANSFER", "TRANSFER", "TRANSFER"],
        "currency": ["INR"] * 8
    })


def test_cleaner_filters_dirty_records(dirty_transaction_data):
    cleaner = TransactionCleaner()
    clean_df, report = cleaner.clean(dirty_transaction_data)

    # From 8 initial rows:
    # - 1 duplicate (TX02 second copy)
    # - 2 null keys (TX03 missing sender, TX04 missing receiver)
    # - 1 self-transfer (TX05)
    # - 2 invalid amounts (TX06 <= 0, TX07 <= 0)
    # Valid remaining: TX01 and TX02
    assert len(clean_df) == 2
    assert report.duplicate_rows_removed >= 1
    assert report.null_keys_removed == 2
    assert report.self_transfers_removed == 1
    assert report.invalid_amounts_removed == 2
    assert "ACC1" in clean_df["sender_account"].values
    assert "ACC2" in clean_df["sender_account"].values


def test_cleaner_imputation_and_uppercase():
    df = pd.DataFrame({
        "transaction_id": ["TX100"],
        "sender_account": ["ACC10"],
        "receiver_account": ["ACC20"],
        "amount": [999.0],
        "timestamp": ["2025-05-10 12:30:00"],
        "channel": [None],
        "location": [" mumbai "],
        "merchant_category": [None],
        "transaction_type": ["transfer"],
        "currency": ["inr"]
    })
    cleaner = TransactionCleaner()
    clean_df, report = cleaner.clean(df)

    assert clean_df.iloc[0]["channel"] == "UNKNOWN"
    assert clean_df.iloc[0]["merchant_category"] == "UNKNOWN"
    assert clean_df.iloc[0]["location"] == "MUMBAI"
    assert clean_df.iloc[0]["transaction_type"] == "TRANSFER"
    assert clean_df.iloc[0]["currency"] == "INR"


def test_temporal_train_test_split():
    timestamps = pd.date_range(start="2025-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "amount": [100.0] * 100
    })
    train_df, test_df = temporal_train_test_split(df, test_ratio=0.2)

    assert len(train_df) == 80
    assert len(test_df) == 20
    # Strict temporal ordering: train max <= test min
    assert train_df["timestamp"].max() < test_df["timestamp"].min()


def test_preprocessor_fit_transform_and_unseen_categories():
    train_df = pd.DataFrame({
        "amount": [100.0, 500.0, 1000.0, 25000.0],
        "timestamp": pd.date_range("2025-01-01", periods=4, freq="h"),
        "transaction_type": ["TRANSFER", "PAYMENT", "TRANSFER", "DEPOSIT"],
        "channel": ["ONLINE", "MOBILE", "BRANCH", "ONLINE"],
        "merchant_category": ["FINANCIAL", "RETAIL", "FOOD", "TRAVEL"],
        "currency": ["INR", "INR", "INR", "INR"]
    })

    preprocessor = DataPreprocessor()
    X_train = preprocessor.fit_transform(train_df)

    assert isinstance(X_train, np.ndarray)
    assert X_train.shape[0] == 4
    assert len(preprocessor.feature_names_) == X_train.shape[1]

    # Test with unseen categorical levels in test data (e.g. channel "ATM", new merchant "CRYPTO")
    test_df = pd.DataFrame({
        "amount": [750.0],
        "timestamp": [pd.Timestamp("2025-02-01 14:00:00")],
        "transaction_type": ["UNKNOWN_TYPE"],
        "channel": ["ATM"],
        "merchant_category": ["CRYPTO_NEW"],
        "currency": ["INR"]
    })

    # Transform must not raise error, must return matrix with exact same column count
    X_test = preprocessor.transform(test_df)
    assert X_test.shape[0] == 1
    assert X_test.shape[1] == X_train.shape[1]
    assert not np.isnan(X_test).any()


def test_preprocessor_serialization(tmp_path):
    train_df = pd.DataFrame({
        "amount": [200.0, 800.0, 1200.0],
        "timestamp": pd.date_range("2025-03-01", periods=3, freq="h"),
        "transaction_type": ["TRANSFER", "PAYMENT", "TRANSFER"],
        "channel": ["ONLINE", "MOBILE", "ONLINE"],
        "merchant_category": ["FINANCIAL", "RETAIL", "FOOD"],
        "currency": ["INR", "INR", "INR"]
    })

    preprocessor = DataPreprocessor()
    preprocessor.fit(train_df)

    save_file = tmp_path / "test_preprocessor.joblib"
    preprocessor.save(save_file)
    assert save_file.exists()

    loaded = DataPreprocessor.load(save_file)
    assert loaded.is_fitted is True
    assert loaded.feature_names_ == preprocessor.feature_names_

    matrix_orig = preprocessor.transform(train_df)
    matrix_loaded = loaded.transform(train_df)
    np.testing.assert_allclose(matrix_orig, matrix_loaded)
