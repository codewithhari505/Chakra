"""
Synthetic Transaction Data Generator — Phase 2 Implementation.

Generates realistic synthetic financial transaction datasets intentionally embedded
with known Anti-Money-Laundering (AML) topologies and typologies:
  1. Layering (A -> B -> C -> D -> E in short succession with fee slippage)
  2. Circular Fund Transfers (A -> B -> C -> A cycles)
  3. Rapid Movement of Funds / Fan-out (Large deposit followed by immediate multi-counterparty dispersion)
  4. Structuring / Smurfing (Transactions clustered just below reporting thresholds, e.g. INR 90,000 - 99,500)
  5. Unusual Account-to-Account Outliers (High amount, foreign/rare geo deviation, anomalous channel)

Usage:
    python scripts/generate_data.py --num-transactions 100000 --num-accounts 10000 --seed 42
"""

import argparse
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DataGenerator")

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Surat", "Kochi",
    "Chandigarh", "Bhopal", "Indore", "Nagpur", "Visakhapatnam", "Coimbatore"
]

TRANSACTION_TYPES = ["TRANSFER", "DEPOSIT", "WITHDRAWAL", "PAYMENT", "ATM"]
TRANSACTION_TYPE_WEIGHTS = [0.55, 0.15, 0.10, 0.15, 0.05]

CHANNELS = ["ONLINE", "MOBILE", "BRANCH", "ATM", "POS"]
CHANNEL_WEIGHTS = [0.45, 0.35, 0.10, 0.05, 0.05]

MERCHANT_CATEGORIES = [
    "FINANCIAL", "RETAIL", "FOOD", "TRAVEL", "UTILITIES",
    "HEALTHCARE", "ENTERTAINMENT", "REAL_ESTATE", "COMMODITIES", "UNKNOWN"
]

ACCOUNT_TYPES = ["INDIVIDUAL", "CORPORATE", "SMALL_BUSINESS", "SHELL_SUSPECT"]
ACCOUNT_TYPE_WEIGHTS = [0.72, 0.20, 0.06, 0.02]

CURRENCY = "INR"

AMOUNT_LOG_MU = 9.2      # Median ~ INR 9,900
AMOUNT_LOG_SIGMA = 1.7   # Wide natural distribution

DATE_START = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
DATE_END = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
TOTAL_TIMEFRAME_SECONDS = int((DATE_END - DATE_START).total_seconds())


def generate_accounts(num_accounts: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    account_ids = [f"ACC{i:05d}" for i in range(1, num_accounts + 1)]

    reg_start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    reg_end = datetime(2024, 12, 31, tzinfo=timezone.utc)
    span_days = (reg_end - reg_start).days

    registration_dates = [
        (reg_start + timedelta(days=int(d))).strftime("%Y-%m-%d %H:%M:%S")
        for d in rng.integers(0, span_days, size=num_accounts)
    ]

    types = rng.choice(ACCOUNT_TYPES, size=num_accounts, p=ACCOUNT_TYPE_WEIGHTS)
    cities = rng.choice(INDIAN_CITIES, size=num_accounts)

    df = pd.DataFrame({
        "account_id": account_ids,
        "account_type": types,
        "country": ["India"] * num_accounts,
        "city": cities,
        "registration_date": registration_dates,
        "risk_score": None,
        "risk_level": None,
        "is_flagged": False,
    })
    logger.info("Generated %d synthetic accounts.", num_accounts)
    return df


def generate_normal_transactions(
    target_count: int,
    account_ids: List[str],
    seed: int = 42
) -> List[Dict]:
    rng = np.random.default_rng(seed)
    acc_array = np.array(account_ids)
    n = target_count

    senders = rng.choice(acc_array, size=n)
    receivers = rng.choice(acc_array, size=n)
    collision_mask = senders == receivers
    while np.any(collision_mask):
        receivers[collision_mask] = rng.choice(acc_array, size=np.sum(collision_mask))
        collision_mask = senders == receivers

    amounts = np.round(rng.lognormal(mean=AMOUNT_LOG_MU, sigma=AMOUNT_LOG_SIGMA, size=n), 2)
    amounts = np.clip(amounts, 50.0, 500000.0)

    time_offsets = rng.integers(0, TOTAL_TIMEFRAME_SECONDS, size=n)
    timestamps = [
        DATE_START + timedelta(seconds=int(s))
        for s in time_offsets
    ]

    types = rng.choice(TRANSACTION_TYPES, size=n, p=TRANSACTION_TYPE_WEIGHTS)
    channels = rng.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)
    locations = rng.choice(INDIAN_CITIES, size=n)
    dev_ids = [f"DEV{rng.integers(1000, 9999):04d}" for _ in range(n)]
    merchants = rng.choice(MERCHANT_CATEGORIES, size=n)

    records = []
    for i in range(n):
        records.append({
            "sender_account": senders[i],
            "receiver_account": receivers[i],
            "amount": float(amounts[i]),
            "timestamp": timestamps[i],
            "transaction_type": types[i],
            "currency": CURRENCY,
            "location": locations[i],
            "channel": channels[i],
            "device_id": dev_ids[i],
            "merchant_category": merchants[i],
            "is_suspicious": False,
            "pattern_type": "NORMAL",
            "pattern_group_id": None
        })
    return records


def inject_layering_patterns(
    account_ids: List[str],
    num_patterns: int,
    rng: np.random.Generator
) -> List[Dict]:
    """
    Pattern 1: Layering Chain (A -> B -> C -> D -> E)
    Hops: 3 to 6 intermediary accounts in rapid succession (5 - 45 mins between hops).
    Amount slightly diminishes (retained fee/commission: 0.5% - 2% cut per hop).
    """
    pattern_records = []
    for p_idx in range(num_patterns):
        chain_len = rng.integers(4, 7)  # 4 to 6 accounts => 3 to 5 hops
        chain_accounts = rng.choice(account_ids, size=chain_len, replace=False)
        base_amount = float(rng.uniform(250000.0, 3500000.0))
        start_ts = DATE_START + timedelta(seconds=int(rng.integers(0, TOTAL_TIMEFRAME_SECONDS - 86400)))
        group_id = f"LAYERING_{p_idx+1:04d}"

        curr_amount = base_amount
        curr_ts = start_ts
        device = f"DEV_LAY_{rng.integers(1000, 9999)}"

        for hop in range(chain_len - 1):
            snd = chain_accounts[hop]
            rcv = chain_accounts[hop + 1]
            # Time delta between 5 and 40 minutes
            step_mins = int(rng.integers(5, 40))
            curr_ts = curr_ts + timedelta(minutes=step_mins)
            # Fee deduction 0.5% - 1.5%
            cut = curr_amount * rng.uniform(0.005, 0.015)
            curr_amount = round(curr_amount - cut, 2)

            pattern_records.append({
                "sender_account": snd,
                "receiver_account": rcv,
                "amount": float(curr_amount),
                "timestamp": curr_ts,
                "transaction_type": "TRANSFER",
                "currency": CURRENCY,
                "location": rng.choice(INDIAN_CITIES),
                "channel": "ONLINE",
                "device_id": device,
                "merchant_category": "FINANCIAL",
                "is_suspicious": True,
                "pattern_type": "LAYERING",
                "pattern_group_id": group_id
            })
    return pattern_records


def inject_circular_transfers(
    account_ids: List[str],
    num_patterns: int,
    rng: np.random.Generator
) -> List[Dict]:
    """
    Pattern 2: Circular Transfers (A -> B -> C -> A or A -> B -> C -> D -> A)
    Detects cycle topologies in transaction graphs with consistent capital.
    """
    pattern_records = []
    for p_idx in range(num_patterns):
        cycle_len = rng.integers(3, 6) # 3 to 5 nodes
        cycle_accs = list(rng.choice(account_ids, size=cycle_len, replace=False))
        # Form cycle by appending start node at the end
        cycle_nodes = cycle_accs + [cycle_accs[0]]

        base_amount = float(rng.uniform(300000.0, 2500000.0))
        curr_ts = DATE_START + timedelta(seconds=int(rng.integers(0, TOTAL_TIMEFRAME_SECONDS - 86400)))
        group_id = f"CIRCULAR_{p_idx+1:04d}"

        curr_amount = base_amount
        for hop in range(len(cycle_nodes) - 1):
            snd = cycle_nodes[hop]
            rcv = cycle_nodes[hop + 1]
            curr_ts = curr_ts + timedelta(minutes=int(rng.integers(10, 60)))
            curr_amount = round(curr_amount * rng.uniform(0.985, 0.998), 2)

            pattern_records.append({
                "sender_account": snd,
                "receiver_account": rcv,
                "amount": float(curr_amount),
                "timestamp": curr_ts,
                "transaction_type": "TRANSFER",
                "currency": CURRENCY,
                "location": rng.choice(INDIAN_CITIES),
                "channel": "ONLINE",
                "device_id": f"DEV_CIRC_{rng.integers(1000, 9999)}",
                "merchant_category": "FINANCIAL",
                "is_suspicious": True,
                "pattern_type": "CIRCULAR_TRANSFER",
                "pattern_group_id": group_id
            })
    return pattern_records


def inject_rapid_movement_patterns(
    account_ids: List[str],
    num_patterns: int,
    rng: np.random.Generator
) -> List[Dict]:
    """
    Pattern 3: Rapid Movement of Funds / Fan-Out dispersion
    Account A receives a substantial inflow, then immediately disperses (within 2-15 mins)
    to 3 to 6 distinct accounts.
    """
    pattern_records = []
    for p_idx in range(num_patterns):
        hub_acc = rng.choice(account_ids)
        remaining = [acc for acc in account_ids if acc != hub_acc]
        inflow_source = rng.choice(remaining)
        num_targets = rng.integers(3, 7)
        targets = rng.choice([acc for acc in remaining if acc != inflow_source], size=num_targets, replace=False)

        total_inflow = float(rng.uniform(600000.0, 5000000.0))
        inflow_ts = DATE_START + timedelta(seconds=int(rng.integers(0, TOTAL_TIMEFRAME_SECONDS - 86400)))
        group_id = f"RAPID_DISPERSION_{p_idx+1:04d}"

        # Inflow transaction
        pattern_records.append({
            "sender_account": inflow_source,
            "receiver_account": hub_acc,
            "amount": round(total_inflow, 2),
            "timestamp": inflow_ts,
            "transaction_type": "TRANSFER",
            "currency": CURRENCY,
            "location": rng.choice(INDIAN_CITIES),
            "channel": "ONLINE",
            "device_id": f"DEV_RAP_{rng.integers(1000, 9999)}",
            "merchant_category": "FINANCIAL",
            "is_suspicious": True,
            "pattern_type": "RAPID_MOVEMENT",
            "pattern_group_id": group_id
        })

        # Multi-target rapid outflow within minutes
        slice_amount = round((total_inflow * 0.98) / num_targets, 2)
        outflow_ts = inflow_ts
        for tgt in targets:
            outflow_ts = outflow_ts + timedelta(seconds=int(rng.integers(30, 240))) # 30s to 4 mins
            jittered_amt = round(slice_amount * rng.uniform(0.96, 1.04), 2)
            pattern_records.append({
                "sender_account": hub_acc,
                "receiver_account": tgt,
                "amount": float(jittered_amt),
                "timestamp": outflow_ts,
                "transaction_type": "TRANSFER",
                "currency": CURRENCY,
                "location": rng.choice(INDIAN_CITIES),
                "channel": "MOBILE",
                "device_id": f"DEV_RAP_{rng.integers(1000, 9999)}",
                "merchant_category": "FINANCIAL",
                "is_suspicious": True,
                "pattern_type": "RAPID_MOVEMENT",
                "pattern_group_id": group_id
            })
    return pattern_records


def inject_structuring_patterns(
    account_ids: List[str],
    num_patterns: int,
    rng: np.random.Generator
) -> List[Dict]:
    """
    Pattern 4: Structuring / Smurfing
    Intentional breaking down of transactions below threshold (e.g. INR 100,000 reporting threshold).
    Transactions between INR 91,000 and INR 99,500 clustered in a short time window (e.g. 1 to 48 hours).
    """
    pattern_records = []
    for p_idx in range(num_patterns):
        snd = rng.choice(account_ids)
        rcv = rng.choice([acc for acc in account_ids if acc != snd])
        num_splits = rng.integers(4, 9) # 4 to 8 split transactions
        base_ts = DATE_START + timedelta(seconds=int(rng.integers(0, TOTAL_TIMEFRAME_SECONDS - 172800)))
        group_id = f"STRUCTURING_{p_idx+1:04d}"

        curr_ts = base_ts
        for _ in range(num_splits):
            curr_ts = curr_ts + timedelta(minutes=int(rng.integers(15, 360)))
            # Structuring amount just below INR 100,000 threshold
            split_amount = round(float(rng.uniform(91000.0, 99600.0)), 2)
            pattern_records.append({
                "sender_account": snd,
                "receiver_account": rcv,
                "amount": split_amount,
                "timestamp": curr_ts,
                "transaction_type": rng.choice(["DEPOSIT", "TRANSFER", "PAYMENT"]),
                "currency": CURRENCY,
                "location": rng.choice(INDIAN_CITIES),
                "channel": rng.choice(["BRANCH", "ATM", "ONLINE"]),
                "device_id": f"DEV_STRUCT_{rng.integers(1000, 9999)}",
                "merchant_category": "FINANCIAL",
                "is_suspicious": True,
                "pattern_type": "STRUCTURING",
                "pattern_group_id": group_id
            })
    return pattern_records


def inject_unusual_outliers(
    account_ids: List[str],
    num_patterns: int,
    rng: np.random.Generator
) -> List[Dict]:
    """
    Pattern 5: High-Value Anomaly / Unusual Account-to-Account Outlier
    Extreme anomalous transaction amounts (e.g. INR 4,000,000 to INR 15,000,000),
    sudden counterparty shifts, rare high-risk merchant or channel combos.
    """
    pattern_records = []
    for p_idx in range(num_patterns):
        snd = rng.choice(account_ids)
        rcv = rng.choice([acc for acc in account_ids if acc != snd])
        anom_ts = DATE_START + timedelta(seconds=int(rng.integers(0, TOTAL_TIMEFRAME_SECONDS)))
        anom_amount = round(float(rng.uniform(4500000.0, 15000000.0)), 2)
        group_id = f"OUTLIER_{p_idx+1:04d}"

        pattern_records.append({
            "sender_account": snd,
            "receiver_account": rcv,
            "amount": anom_amount,
            "timestamp": anom_ts,
            "transaction_type": "TRANSFER",
            "currency": CURRENCY,
            "location": rng.choice(["Dubai", "Singapore", "Zurich", "Cayman", "Panama"] + INDIAN_CITIES),
            "channel": "ONLINE",
            "device_id": f"DEV_ANOM_{rng.integers(1000, 9999)}",
            "merchant_category": rng.choice(["COMMODITIES", "REAL_ESTATE", "FINANCIAL"]),
            "is_suspicious": True,
            "pattern_type": "UNUSUAL_OUTLIER",
            "pattern_group_id": group_id
        })
    return pattern_records


def generate_full_dataset(
    num_transactions: int,
    num_accounts: int,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    # 1. Accounts
    accounts_df = generate_accounts(num_accounts, seed=seed)
    account_ids = accounts_df["account_id"].tolist()

    # Determine scale of suspicious patterns (~6-8% of total dataset)
    # Budget breakdown:
    target_suspicious = int(num_transactions * 0.075)
    
    num_layering = max(20, int(target_suspicious * 0.25 / 5))
    num_circular = max(20, int(target_suspicious * 0.20 / 4))
    num_rapid = max(25, int(target_suspicious * 0.25 / 5))
    num_struct = max(25, int(target_suspicious * 0.20 / 6))
    num_outliers = max(30, int(target_suspicious * 0.10))

    logger.info("Injecting AML typologies with target ~%d suspicious txns...", target_suspicious)

    suspicious_records: List[Dict] = []
    suspicious_records.extend(inject_layering_patterns(account_ids, num_layering, rng))
    suspicious_records.extend(inject_circular_transfers(account_ids, num_circular, rng))
    suspicious_records.extend(inject_rapid_movement_patterns(account_ids, num_rapid, rng))
    suspicious_records.extend(inject_structuring_patterns(account_ids, num_struct, rng))
    suspicious_records.extend(inject_unusual_outliers(account_ids, num_outliers, rng))

    actual_suspicious_count = len(suspicious_records)
    normal_count = max(0, num_transactions - actual_suspicious_count)

    logger.info("Generating %d normal background transactions...", normal_count)
    normal_records = generate_normal_transactions(normal_count, account_ids, seed=seed)

    all_records = normal_records + suspicious_records
    rng.shuffle(all_records)

    # Assign sequential transaction IDs and format timestamps
    transactions_df = pd.DataFrame(all_records)
    transactions_df = transactions_df.sort_values(by="timestamp").reset_index(drop=True)
    transactions_df["transaction_id"] = [f"TX{i+1:07d}" for i in range(len(transactions_df))]
    transactions_df["timestamp"] = transactions_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Column ordering according to spec
    ordered_cols = [
        "transaction_id",
        "sender_account",
        "receiver_account",
        "amount",
        "timestamp",
        "transaction_type",
        "currency",
        "location",
        "channel",
        "device_id",
        "merchant_category",
        "is_suspicious",
        "pattern_type",
        "pattern_group_id"
    ]
    transactions_df = transactions_df[ordered_cols]

    # Flag high-risk accounts in account metadata
    suspicious_senders = set(transactions_df[transactions_df["is_suspicious"]]["sender_account"].unique())
    suspicious_receivers = set(transactions_df[transactions_df["is_suspicious"]]["receiver_account"].unique())
    all_suspicious_accs = suspicious_senders.union(suspicious_receivers)
    accounts_df["is_flagged"] = accounts_df["account_id"].isin(all_suspicious_accs)

    return transactions_df, accounts_df


def save_dataset(
    transactions_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    output_dir: Path
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    txn_path = output_dir / "transactions.csv"
    acc_path = output_dir / "accounts.csv"

    transactions_df.to_csv(txn_path, index=False)
    accounts_df.to_csv(acc_path, index=False)

    logger.info("Saved transactions to: %s (%d rows)", txn_path, len(transactions_df))
    logger.info("Saved accounts to:     %s (%d rows)", acc_path, len(accounts_df))

    suspicious_mask = transactions_df["is_suspicious"] == True
    logger.info("================ DATASET GENERATION SUMMARY ================")
    logger.info("Total Transactions : %d", len(transactions_df))
    logger.info("Suspicious Rows    : %d (%.2f%%)", suspicious_mask.sum(), (suspicious_mask.sum() / len(transactions_df)) * 100)
    logger.info("Normal Rows        : %d (%.2f%%)", (~suspicious_mask).sum(), ((~suspicious_mask).sum() / len(transactions_df)) * 100)
    logger.info("Total Accounts     : %d", len(accounts_df))
    logger.info("Flagged Accounts   : %d", accounts_df["is_flagged"].sum())
    logger.info("Breakdown by Pattern Type:")
    for ptype, count in transactions_df["pattern_type"].value_counts().items():
        logger.info("  - %-20s: %d", ptype, count)
    logger.info("Amount Range       : INR %.2f - INR %.2f", transactions_df["amount"].min(), transactions_df["amount"].max())
    logger.info("Time Range         : %s to %s", transactions_df["timestamp"].min(), transactions_df["timestamp"].max())
    logger.info("============================================================")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic AML transaction dataset.")
    parser.add_argument("--num-transactions", type=int, default=100000, help="Total transaction count (default: 100,000)")
    parser.add_argument("--num-accounts", type=int, default=10000, help="Total account count (default: 10,000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(ROOT / "ml" / "data" / "synthetic"),
        help="Target directory for output CSVs"
    )
    args = parser.parse_args()

    txns_df, accs_df = generate_full_dataset(
        num_transactions=args.num_transactions,
        num_accounts=args.num_accounts,
        seed=args.seed
    )
    save_dataset(txns_df, accs_df, Path(args.output_dir))


if __name__ == "__main__":
    main()
