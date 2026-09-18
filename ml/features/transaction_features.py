"""
Transaction-Level Feature Engineering — Phase 4.

Calculates fine-grained transaction and temporal-window features:
  - Base numerical & log-transformed amounts
  - Temporal cyclical and risk indicators (hour, day, weekend, night)
  - Time-window rolling features (1 hour, 24 hours, 7 days) without future lookahead
  - Deviation from moving average transaction value
  - Inflow vs outflow velocity ratios
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("TransactionFeatures")


def extract_transaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes transaction-level and rolling window features for an AML dataset.
    Input DataFrame must have columns: ['transaction_id', 'sender_account', 'receiver_account', 'amount', 'timestamp'].
    Output retains transaction_id and appends all engineered transaction features.
    """
    logger.info("Extracting transaction-level features for %d rows...", len(df))
    df_work = df.copy()

    # Ensure datetime format and remove tzinfo for consistent timedelta math
    if not pd.api.types.is_datetime64_any_dtype(df_work["timestamp"]):
        df_work["timestamp"] = pd.to_datetime(df_work["timestamp"])
    if getattr(df_work["timestamp"].dt, "tz", None) is not None:
        df_work["timestamp"] = df_work["timestamp"].dt.tz_localize(None)

    df_work = df_work.sort_values(by="timestamp").reset_index(drop=True)
    df_work["amount"] = pd.to_numeric(df_work["amount"], errors="coerce").fillna(0.0)

    n_rows = len(df_work)
    df_work["_orig_idx"] = np.arange(n_rows)

    # 1. Base Amount Features
    df_work["transaction_amount"] = df_work["amount"]
    df_work["log_transaction_amount"] = np.log1p(df_work["amount"])

    # 2. Temporal & Cyclical Features
    df_work["transaction_hour"] = df_work["timestamp"].dt.hour
    df_work["transaction_day"] = df_work["timestamp"].dt.day
    df_work["transaction_day_of_week"] = df_work["timestamp"].dt.dayofweek
    df_work["is_weekend"] = df_work["transaction_day_of_week"].isin([5, 6]).astype(int)
    df_work["is_night"] = df_work["transaction_hour"].apply(lambda h: 1 if h >= 23 or h <= 5 else 0)

    # 3. Rolling Time-Window Features for Outflows (Sender Account)
    # Using group index mapping guarantees exact row alignment with zero lookahead bias
    df_indexed = df_work.set_index("timestamp")

    sender_order = df_work.groupby("sender_account", observed=False)["_orig_idx"].apply(list).explode().values.astype(int)
    sender_rolling = df_indexed.groupby("sender_account", observed=False)["amount"]

    # 1h, 24h, 7d rolling calculations
    cnt_1h_vals = np.nan_to_num(sender_rolling.rolling("1h", closed="left").count().values, nan=0.0)
    cnt_24h_vals = np.nan_to_num(sender_rolling.rolling("24h", closed="left").count().values, nan=0.0)
    sum_24h_vals = np.nan_to_num(sender_rolling.rolling("24h", closed="left").sum().values, nan=0.0)
    cnt_7d_vals = np.nan_to_num(sender_rolling.rolling("7D", closed="left").count().values, nan=0.0)
    avg_7d_vals = np.nan_to_num(sender_rolling.rolling("7D", closed="left").mean().values, nan=0.0)

    # Vectorized assignment to original row positions
    txn_count_1h = np.zeros(n_rows)
    txn_count_24h = np.zeros(n_rows)
    outflow_amount_24h = np.zeros(n_rows)
    txn_count_7d = np.zeros(n_rows)
    sender_avg_7d = np.zeros(n_rows)

    txn_count_1h[sender_order] = cnt_1h_vals
    txn_count_24h[sender_order] = cnt_24h_vals
    outflow_amount_24h[sender_order] = sum_24h_vals
    txn_count_7d[sender_order] = cnt_7d_vals
    sender_avg_7d[sender_order] = avg_7d_vals

    df_work["transaction_count_1h"] = txn_count_1h
    df_work["transaction_count_24h"] = txn_count_24h
    df_work["outflow_amount_24h"] = outflow_amount_24h
    df_work["transaction_count_7d"] = txn_count_7d
    df_work["sender_avg_amount_7d"] = sender_avg_7d

    # 4. Amount Deviation from Historical 7-day Moving Average
    prior_avg = np.where(df_work["sender_avg_amount_7d"] > 0, df_work["sender_avg_amount_7d"], np.nan)
    df_work["amount_deviation"] = np.nan_to_num(df_work["amount"] / prior_avg, nan=1.0)
    df_work["log_amount_deviation"] = np.log1p(df_work["amount_deviation"])

    # 5. Inflow Rolling 24h for Receiver Account
    receiver_order = df_work.groupby("receiver_account", observed=False)["_orig_idx"].apply(list).explode().values.astype(int)
    recv_rolling = df_indexed.groupby("receiver_account", observed=False)["amount"]
    recv_sum_24h_vals = np.nan_to_num(recv_rolling.rolling("24h", closed="left").sum().values, nan=0.0)

    inflow_amount_24h = np.zeros(n_rows)
    inflow_amount_24h[receiver_order] = recv_sum_24h_vals
    df_work["inflow_amount_24h"] = inflow_amount_24h

    # 6. Inflow / Outflow Balance Ratio
    df_work["inflow_outflow_ratio"] = (df_work["inflow_amount_24h"] + 1.0) / (df_work["outflow_amount_24h"] + 1.0)

    # Bound extreme ratios
    df_work["amount_deviation"] = df_work["amount_deviation"].clip(upper=100.0)
    df_work["inflow_outflow_ratio"] = df_work["inflow_outflow_ratio"].clip(upper=100.0)

    feature_cols = [
        "transaction_id",
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
    ]

    logger.info("Transaction feature extraction complete: %d features computed.", len(feature_cols) - 1)
    return df_work[feature_cols]
