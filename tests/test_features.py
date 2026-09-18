"""
Unit tests for Phase 4: Feature Engineering Modules.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.features.transaction_features import extract_transaction_features
from ml.features.behavioral_features import extract_behavioral_features
from ml.features.build_features import generate_feature_set


@pytest.fixture
def sample_transaction_stream():
    """Generates a small chronological stream of transactions with known timestamps."""
    base_time = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    return pd.DataFrame({
        "transaction_id": ["TX1", "TX2", "TX3", "TX4", "TX5"],
        "sender_account": ["ACC_A", "ACC_A", "ACC_B", "ACC_A", "ACC_B"],
        "receiver_account": ["ACC_B", "ACC_C", "ACC_A", "ACC_D", "ACC_A"],
        "amount": [1000.0, 2000.0, 5000.0, 15000.0, 500.0],
        "timestamp": [
            base_time,                                  # T0
            base_time + timedelta(minutes=30),          # T0 + 30m
            base_time + timedelta(hours=2),             # T0 + 2h
            base_time + timedelta(hours=5),             # T0 + 5h
            base_time + timedelta(days=2),              # T0 + 48h
        ],
        "transaction_type": ["TRANSFER"] * 5,
        "channel": ["ONLINE"] * 5,
        "currency": ["INR"] * 5
    })


def test_transaction_feature_extraction(sample_transaction_stream):
    feats = extract_transaction_features(sample_transaction_stream)

    expected_cols = [
        "transaction_id", "transaction_amount", "log_transaction_amount",
        "transaction_hour", "transaction_day", "transaction_day_of_week",
        "is_weekend", "is_night", "transaction_count_1h", "transaction_count_24h",
        "transaction_count_7d", "outflow_amount_24h", "inflow_amount_24h",
        "amount_deviation", "inflow_outflow_ratio"
    ]
    for col in expected_cols:
        assert col in feats.columns, f"Missing feature: {col}"

    # Verify no NaN values in features
    assert not feats[expected_cols].isnull().any().any()

    # ACC_A sends at T0, T0+30m, T0+5h:
    # At T0+30m (TX2), prior 1h count for ACC_A must be exactly 1 (TX1)
    tx2_row = feats[feats["transaction_id"] == "TX2"].iloc[0]
    assert tx2_row["transaction_count_1h"] == 1
    assert tx2_row["transaction_count_24h"] == 1

    # At T0+5h (TX4), prior 24h count for ACC_A must be 2 (TX1 and TX2)
    tx4_row = feats[feats["transaction_id"] == "TX4"].iloc[0]
    assert tx4_row["transaction_count_24h"] == 2
    assert tx4_row["outflow_amount_24h"] == 3000.0  # 1000 + 2000


def test_behavioral_feature_extraction(sample_transaction_stream):
    accounts_df = pd.DataFrame({
        "account_id": ["ACC_A", "ACC_B", "ACC_C", "ACC_D"],
        "registration_date": ["2024-01-01 00:00:00"] * 4
    })
    behav = extract_behavioral_features(sample_transaction_stream, accounts_df=accounts_df)

    expected_cols = [
        "transaction_id", "account_age_days", "total_sender_txns",
        "cumulative_outflow", "sender_avg_txn_size", "sender_max_txn_size",
        "receiver_cumulative_inflow", "unique_receivers_count",
        "unique_senders_count", "transaction_velocity", "unusual_transaction_ratio"
    ]
    for col in expected_cols:
        assert col in behav.columns, f"Missing behavioral feature: {col}"

    assert not behav[expected_cols].isnull().any().any()

    # Verify cumulative sender txn counts
    # ACC_A has 3 txns total: TX1 (count=1), TX2 (count=2), TX4 (count=3)
    tx4_row = behav[behav["transaction_id"] == "TX4"].iloc[0]
    assert tx4_row["total_sender_txns"] == 3
    assert tx4_row["cumulative_outflow"] == 18000.0  # 1000 + 2000 + 15000
    assert tx4_row["sender_max_txn_size"] == 15000.0


def test_generate_feature_set_integration(sample_transaction_stream):
    merged = generate_feature_set(sample_transaction_stream)
    assert len(merged) == len(sample_transaction_stream)
    assert "amount_deviation" in merged.columns
    assert "transaction_velocity" in merged.columns
    assert "inflow_outflow_ratio" in merged.columns
    assert not merged["transaction_amount"].isnull().any()
