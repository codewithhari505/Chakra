"""
Data Cleaning and Validation Pipeline — Phase 3.

Handles raw transaction data ingestion, schema validation, deduplication,
invalid record filtering, timestamp normalization, and data health reporting.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("DataCleaner")


@dataclass
class CleaningReport:
    """Audit metrics produced during transaction data cleaning."""
    initial_rows: int = 0
    final_rows: int = 0
    duplicate_rows_removed: int = 0
    null_keys_removed: int = 0
    invalid_amounts_removed: int = 0
    self_transfers_removed: int = 0
    invalid_timestamps_removed: int = 0
    missing_fields_imputed: Dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        retained_pct = (self.final_rows / self.initial_rows * 100) if self.initial_rows > 0 else 0
        return (
            f"--- Data Cleaning Audit Report ---\n"
            f"Initial Records          : {self.initial_rows}\n"
            f"Final Valid Records      : {self.final_rows} ({retained_pct:.2f}% retained)\n"
            f"Duplicates Removed       : {self.duplicate_rows_removed}\n"
            f"Null Account Keys        : {self.null_keys_removed}\n"
            f"Invalid Amounts (<=0)    : {self.invalid_amounts_removed}\n"
            f"Self-Transfers (A -> A)  : {self.self_transfers_removed}\n"
            f"Invalid Timestamps       : {self.invalid_timestamps_removed}\n"
            f"Missing Fields Imputed   : {self.missing_fields_imputed}\n"
            f"----------------------------------"
        )


class TransactionCleaner:
    """
    Validates and cleans raw transaction data frames according to AML data integrity rules.
    """

    DEFAULT_IMPUTATIONS = {
        "channel": "UNKNOWN",
        "location": "UNKNOWN",
        "device_id": "UNKNOWN",
        "merchant_category": "UNKNOWN",
        "currency": "INR",
        "transaction_type": "TRANSFER",
    }

    def __init__(self, imputations: Optional[Dict[str, str]] = None):
        self.imputations = imputations or self.DEFAULT_IMPUTATIONS

    def clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Executes complete cleaning pipeline on the input DataFrame.
        Returns the cleaned DataFrame and a CleaningReport audit object.
        """
        report = CleaningReport(initial_rows=len(df))
        df_clean = df.copy()

        # 1. Deduplication by transaction_id
        if "transaction_id" in df_clean.columns:
            initial_count = len(df_clean)
            df_clean = df_clean.drop_duplicates(subset=["transaction_id"], keep="first")
            report.duplicate_rows_removed += initial_count - len(df_clean)

        # Also remove exact content duplicates
        initial_count = len(df_clean)
        content_cols = [c for c in ["sender_account", "receiver_account", "amount", "timestamp"] if c in df_clean.columns]
        if content_cols:
            df_clean = df_clean.drop_duplicates(subset=content_cols, keep="first")
            report.duplicate_rows_removed += initial_count - len(df_clean)

        # 2. Key Presence Filtering
        key_mask = df_clean["sender_account"].notna() & df_clean["receiver_account"].notna()
        report.null_keys_removed = int((~key_mask).sum())
        df_clean = df_clean[key_mask]

        # 3. Invalid Amount Filtering (must be numeric and strictly positive)
        df_clean["amount"] = pd.to_numeric(df_clean["amount"], errors="coerce")
        amount_mask = df_clean["amount"].notna() & (df_clean["amount"] > 0)
        report.invalid_amounts_removed = int((~amount_mask).sum())
        df_clean = df_clean[amount_mask]

        # 4. Self-transfer filtering (Sender cannot be receiver in standard AML taxonomy)
        self_transfer_mask = df_clean["sender_account"] == df_clean["receiver_account"]
        report.self_transfers_removed = int(self_transfer_mask.sum())
        df_clean = df_clean[~self_transfer_mask]

        # 5. Timestamp Conversion & Filtering
        df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"], errors="coerce")
        ts_valid_mask = df_clean["timestamp"].notna()
        report.invalid_timestamps_removed = int((~ts_valid_mask).sum())
        df_clean = df_clean[ts_valid_mask]

        # 6. Impute Missing Values for Non-Critical Categorical Metadata
        for col, default_val in self.imputations.items():
            if col in df_clean.columns:
                missing_count = int(df_clean[col].isna().sum())
                if missing_count > 0:
                    df_clean[col] = df_clean[col].fillna(default_val)
                    report.missing_fields_imputed[col] = missing_count
            else:
                df_clean[col] = default_val

        # 7. Standardize Categorical Strings
        str_cols = ["channel", "location", "merchant_category", "transaction_type", "currency"]
        for col in str_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip().str.upper()

        # 8. Sort Chronologically
        df_clean = df_clean.sort_values(by="timestamp").reset_index(drop=True)
        report.final_rows = len(df_clean)

        logger.info(report.summary())
        return df_clean, report
