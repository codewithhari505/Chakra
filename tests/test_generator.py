"""
Unit tests for Phase 2: Synthetic Data Generator and AML Pattern Verification.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate_data import (
    generate_accounts,
    generate_full_dataset,
    inject_layering_patterns,
    inject_circular_transfers,
    inject_rapid_movement_patterns,
    inject_structuring_patterns,
    inject_unusual_outliers
)


def test_generate_accounts_structure():
    accs_df = generate_accounts(num_accounts=200, seed=42)
    assert len(accs_df) == 200
    assert "account_id" in accs_df.columns
    assert "account_type" in accs_df.columns
    assert accs_df["account_id"].nunique() == 200
    assert not accs_df["account_id"].isnull().any()


def test_generator_reproducibility():
    txns_1, accs_1 = generate_full_dataset(num_transactions=1000, num_accounts=100, seed=42)
    txns_2, accs_2 = generate_full_dataset(num_transactions=1000, num_accounts=100, seed=42)

    pd.testing.assert_frame_equal(txns_1, txns_2)
    pd.testing.assert_frame_equal(accs_1, accs_2)


def test_dataset_columns_and_invariants():
    txns, accs = generate_full_dataset(num_transactions=2000, num_accounts=200, seed=123)

    expected_cols = [
        "transaction_id", "sender_account", "receiver_account", "amount",
        "timestamp", "transaction_type", "currency", "location", "channel",
        "device_id", "merchant_category", "is_suspicious", "pattern_type", "pattern_group_id"
    ]
    for col in expected_cols:
        assert col in txns.columns, f"Missing column {col}"

    assert (txns["amount"] > 0).all(), "Transactions must have positive amount"
    assert (txns["sender_account"] != txns["receiver_account"]).all(), "Sender and receiver cannot be identical"
    assert txns["transaction_id"].nunique() == len(txns), "Transaction IDs must be unique"


def test_all_aml_patterns_present():
    txns, accs = generate_full_dataset(num_transactions=3000, num_accounts=300, seed=99)
    pattern_types = set(txns["pattern_type"].unique())
    expected_patterns = {
        "NORMAL",
        "LAYERING",
        "CIRCULAR_TRANSFER",
        "RAPID_MOVEMENT",
        "STRUCTURING",
        "UNUSUAL_OUTLIER"
    }
    assert expected_patterns.issubset(pattern_types)


def test_structuring_threshold_logic():
    rng = np.random.default_rng(42)
    accs = [f"ACC{i:04d}" for i in range(50)]
    struct_txns = inject_structuring_patterns(accs, num_patterns=5, rng=rng)
    assert len(struct_txns) > 0
    for txn in struct_txns:
        assert 90000.0 <= txn["amount"] <= 100000.0
        assert txn["pattern_type"] == "STRUCTURING"
        assert txn["is_suspicious"] is True


def test_circular_transfer_topology():
    rng = np.random.default_rng(42)
    accs = [f"ACC{i:04d}" for i in range(20)]
    circ_txns = inject_circular_transfers(accs, num_patterns=3, rng=rng)
    
    # Group by pattern_group_id and check cycle closure
    df = pd.DataFrame(circ_txns)
    for group_id, group in df.groupby("pattern_group_id"):
        first_sender = group.iloc[0]["sender_account"]
        last_receiver = group.iloc[-1]["receiver_account"]
        assert first_sender == last_receiver, f"Cycle {group_id} not closed (first={first_sender}, last={last_receiver})"
