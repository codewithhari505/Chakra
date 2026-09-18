"""
Account-Level Behavioral Feature Engineering — Phase 4.

Calculates cumulative historical behavioral profiles for accounts:
  - Account age relative to transaction timestamp
  - Lifetime transaction volume and flow balances (total inflow, total outflow)
  - Mean and maximum transaction magnitudes
  - Network counterparty diversity (unique senders and receivers)
  - Velocity (transactions per active day)
  - Behavioral deviation ratio (fraction of transactions > 3x average)
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("BehavioralFeatures")


def extract_behavioral_features(
    df: pd.DataFrame,
    accounts_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Extracts account-level behavioral features mapped to each transaction's sender account.
    Prevents lookahead bias by using expanding cumulative statistics over time.
    """
    logger.info("Extracting account behavioral features for %d transactions...", len(df))
    df_work = df.copy()

    # Normalize timestamp to tz-naive
    if not pd.api.types.is_datetime64_any_dtype(df_work["timestamp"]):
        df_work["timestamp"] = pd.to_datetime(df_work["timestamp"])
    if getattr(df_work["timestamp"].dt, "tz", None) is not None:
        df_work["timestamp"] = df_work["timestamp"].dt.tz_localize(None)

    df_work = df_work.sort_values(by="timestamp").reset_index(drop=True)
    df_work["amount"] = pd.to_numeric(df_work["amount"], errors="coerce").fillna(0.0)

    # 1. Map Account Registration Date if accounts_df is provided
    if accounts_df is not None and "registration_date" in accounts_df.columns:
        acc_meta = accounts_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(acc_meta["registration_date"]):
            acc_meta["registration_date"] = pd.to_datetime(acc_meta["registration_date"])
        if getattr(acc_meta["registration_date"].dt, "tz", None) is not None:
            acc_meta["registration_date"] = acc_meta["registration_date"].dt.tz_localize(None)

        reg_map = acc_meta.set_index("account_id")["registration_date"].to_dict()
        sender_reg = df_work["sender_account"].map(reg_map)
        df_work["account_age_days"] = (df_work["timestamp"] - sender_reg).dt.total_seconds() / 86400.0
        df_work["account_age_days"] = df_work["account_age_days"].fillna(365.0).clip(lower=1.0)
    else:
        first_seen = df_work.groupby("sender_account")["timestamp"].transform("min")
        df_work["account_age_days"] = ((df_work["timestamp"] - first_seen).dt.total_seconds() / 86400.0) + 30.0

    # 2. Expanding Cumulative Statistics for Sender (Outflows)
    sender_gb = df_work.groupby("sender_account", observed=False)

    df_work["total_sender_txns"] = sender_gb.cumcount() + 1
    df_work["cumulative_outflow"] = sender_gb["amount"].cumsum()
    df_work["sender_avg_txn_size"] = df_work["cumulative_outflow"] / df_work["total_sender_txns"]
    df_work["sender_max_txn_size"] = sender_gb["amount"].cummax()

    # 3. Expanding Cumulative Inflows per Receiver
    recv_gb = df_work.groupby("receiver_account", observed=False)
    df_work["receiver_cumulative_inflow"] = recv_gb["amount"].cumsum()
    df_work["receiver_total_txns"] = recv_gb.cumcount() + 1
    df_work["receiver_avg_inflow_size"] = df_work["receiver_cumulative_inflow"] / df_work["receiver_total_txns"]

    # 4. Counterparty Diversity
    df_work["is_new_receiver"] = ~df_work.duplicated(subset=["sender_account", "receiver_account"])
    df_work["unique_receivers_count"] = df_work.groupby("sender_account", observed=False)["is_new_receiver"].cumsum()

    df_work["is_new_sender"] = ~df_work.duplicated(subset=["receiver_account", "sender_account"])
    df_work["unique_senders_count"] = df_work.groupby("receiver_account", observed=False)["is_new_sender"].cumsum()

    # 5. Transaction Velocity
    df_work["transaction_velocity"] = df_work["total_sender_txns"] / (df_work["account_age_days"] + 1.0)

    # 6. Outlier / Behavioral Spike Ratio
    is_spike = (df_work["amount"] >= (3.0 * df_work["sender_avg_txn_size"])).astype(int)
    df_work["_is_spike"] = is_spike
    df_work["unusual_transaction_ratio"] = (
        df_work.groupby("sender_account", observed=False)["_is_spike"].cumsum() / df_work["total_sender_txns"]
    )

    behavioral_cols = [
        "transaction_id",
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

    logger.info("Behavioral feature extraction complete: %d features computed.", len(behavioral_cols) - 1)
    return df_work[behavioral_cols]
