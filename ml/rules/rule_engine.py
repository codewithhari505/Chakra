"""
Rule-Based AML Detection Engine — Phase 5.

Implements transparent, explainable heuristic detection rules governed by:
  - PMLA 2002 statutory limits
  - RBI 2026 KYC Amendment Directions for Indian Financial Institutions
  - Transaction velocity and behavioral deviation thresholds
  - Cybersecurity device and session risk signals

Every triggered rule provides an explicit explanation dictionary for auditability.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ml.rules.regulatory_knowledge import (
    CROSS_BORDER_HIGH_RISK_JURISDICTIONS,
    REGULATORY_FRAMEWORKS,
    RBI_2026_AUTHORIZED_CERTIFIERS,
)

logger = logging.getLogger("RuleEngine")


@dataclass
class RuleResult:
    """Individual triggered rule explanation and audit trail."""
    rule_id: str
    rule_name: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    score_contribution: float
    reason: str
    regulatory_references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "score_contribution": self.score_contribution,
            "reason": self.reason,
            "regulatory_references": self.regulatory_references,
        }


@dataclass
class RuleEvaluation:
    """Consolidated rule-based evaluation outcome for a transaction."""
    rule_score: float  # Normalized 0 to 100
    triggered_count: int
    triggered_rules: List[RuleResult]
    summary_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_score": round(self.rule_score, 2),
            "triggered_count": self.triggered_count,
            "triggered_rules": [r.to_dict() for r in self.triggered_rules],
            "summary_explanation": self.summary_explanation,
        }


class AMLRuleEngine:
    """
    Evaluates rule-based indicators against transaction records and engineered feature contexts.
    """

    def __init__(
        self,
        high_value_threshold: float = 1_000_000.0,
        critical_value_threshold: float = 5_000_000.0,
        structuring_lower: float = 90_000.0,
        structuring_upper: float = 99_999.0,
        velocity_1h_threshold: int = 3,
        velocity_24h_threshold: int = 5,
        deviation_ratio_threshold: float = 4.0,
        night_high_value_threshold: float = 200_000.0,
    ):
        self.high_value_threshold = high_value_threshold
        self.critical_value_threshold = critical_value_threshold
        self.structuring_lower = structuring_lower
        self.structuring_upper = structuring_upper
        self.velocity_1h_threshold = velocity_1h_threshold
        self.velocity_24h_threshold = velocity_24h_threshold
        self.deviation_ratio_threshold = deviation_ratio_threshold
        self.night_high_value_threshold = night_high_value_threshold

    def evaluate_transaction(self, row: Union[pd.Series, Dict[str, Any]]) -> RuleEvaluation:
        """
        Evaluates an individual transaction row against all rule suites.
        Expects keys from raw data or engineered feature set.
        """
        triggered: List[RuleResult] = []

        amount = float(row.get("amount", row.get("transaction_amount", 0.0)))
        tx_hour = int(row.get("transaction_hour", row.get("hour", 12)))
        tx_count_1h = float(row.get("transaction_count_1h", 0.0))
        tx_count_24h = float(row.get("transaction_count_24h", 0.0))
        amt_dev = float(row.get("amount_deviation", 1.0))
        in_out_ratio = float(row.get("inflow_outflow_ratio", 1.0))
        location = str(row.get("location", "UNKNOWN")).upper()
        device_id = str(row.get("device_id", "UNKNOWN"))

        # ---------------------------------------------------------------------
        # RULE 1: High-Value Transaction Threshold (PMLA Statutory Monitoring)
        # ---------------------------------------------------------------------
        if amount >= self.critical_value_threshold:
            triggered.append(RuleResult(
                rule_id="RULE_CRITICAL_HIGH_VALUE",
                rule_name="Critical High-Value Transfer",
                severity="CRITICAL",
                score_contribution=45.0,
                reason=f"Transaction amount INR {amount:,.2f} exceeds critical scrutiny limit of INR {self.critical_value_threshold:,.2f}.",
                regulatory_references=[REGULATORY_FRAMEWORKS["PMLA_2002"], REGULATORY_FRAMEWORKS["BRA_1949"]]
            ))
        elif amount >= self.high_value_threshold:
            triggered.append(RuleResult(
                rule_id="RULE_HIGH_VALUE",
                rule_name="High-Value Financial Transfer",
                severity="HIGH",
                score_contribution=30.0,
                reason=f"Transaction amount INR {amount:,.2f} exceeds reporting limit of INR {self.high_value_threshold:,.2f}.",
                regulatory_references=[REGULATORY_FRAMEWORKS["PMLA_2002"]]
            ))

        # ---------------------------------------------------------------------
        # RULE 2: Structuring / Smurfing Below Regulatory Limit
        # ---------------------------------------------------------------------
        if self.structuring_lower <= amount <= self.structuring_upper:
            severity = "CRITICAL" if tx_count_24h >= 2 else "HIGH"
            score = 40.0 if tx_count_24h >= 2 else 25.0
            triggered.append(RuleResult(
                rule_id="RULE_STRUCTURING_PMLA",
                rule_name="Suspected Structuring / Smurfing Pattern",
                severity=severity,
                score_contribution=score,
                reason=(
                    f"Amount INR {amount:,.2f} is clustered just below the statutory INR 100,000 threshold "
                    f"with {int(tx_count_24h)} prior transfers in 24 hours."
                ),
                regulatory_references=[REGULATORY_FRAMEWORKS["PMLA_2002"], REGULATORY_FRAMEWORKS["PML_RULES_2005"]]
            ))

        # ---------------------------------------------------------------------
        # RULE 3: Rapid Transaction Velocity (Smurfing / Layering burst)
        # ---------------------------------------------------------------------
        if tx_count_1h >= self.velocity_1h_threshold:
            triggered.append(RuleResult(
                rule_id="RULE_RAPID_VELOCITY_1H",
                rule_name="Extreme 1-Hour Transaction Burst",
                severity="HIGH",
                score_contribution=30.0,
                reason=f"{int(tx_count_1h)} outgoing transfers completed within 60 minutes.",
                regulatory_references=[REGULATORY_FRAMEWORKS["PML_RULES_2005"]]
            ))
        elif tx_count_24h >= self.velocity_24h_threshold:
            triggered.append(RuleResult(
                rule_id="RULE_RAPID_VELOCITY_24H",
                rule_name="Elevated 24-Hour Velocity",
                severity="MEDIUM",
                score_contribution=20.0,
                reason=f"{int(tx_count_24h)} transactions recorded by sender in the preceding 24 hours.",
                regulatory_references=[REGULATORY_FRAMEWORKS["PML_RULES_2005"]]
            ))

        # ---------------------------------------------------------------------
        # RULE 4: Behavioral Deviation from Baseline (Outlier from 7d Average)
        # ---------------------------------------------------------------------
        if amt_dev >= self.deviation_ratio_threshold:
            triggered.append(RuleResult(
                rule_id="RULE_BEHAVIORAL_DEVIATION",
                rule_name="Significant Behavioral Deviation",
                severity="HIGH",
                score_contribution=25.0,
                reason=f"Current amount is {amt_dev:.1f}x higher than sender's recent 7-day moving average.",
                regulatory_references=[REGULATORY_FRAMEWORKS["BRA_1949"]]
            ))

        # ---------------------------------------------------------------------
        # RULE 5: Off-Hours High-Value Transaction (Night Window 23:00 - 05:59)
        # ---------------------------------------------------------------------
        if (tx_hour >= 23 or tx_hour <= 5) and amount >= self.night_high_value_threshold:
            triggered.append(RuleResult(
                rule_id="RULE_OFF_HOURS_HIGH_VALUE",
                rule_name="High-Value Night Window Activity",
                severity="MEDIUM",
                score_contribution=15.0,
                reason=f"High-value transfer of INR {amount:,.2f} initiated during nocturnal hours ({tx_hour:02d}:00).",
                regulatory_references=[REGULATORY_FRAMEWORKS["PML_RULES_2005"]]
            ))

        # ---------------------------------------------------------------------
        # RULE 6: Rapid Dispersion / Pass-Through Ratio (Layering Hub)
        # ---------------------------------------------------------------------
        if tx_count_24h >= 2 and (in_out_ratio > 4.0 or in_out_ratio < 0.15):
            triggered.append(RuleResult(
                rule_id="RULE_RAPID_DISPERSION_FLOW",
                rule_name="Rapid Pass-Through / Flow Imbalance",
                severity="HIGH",
                score_contribution=25.0,
                reason=f"Pass-through ratio of {in_out_ratio:.2f} indicates immediate capital transit without retention.",
                regulatory_references=[REGULATORY_FRAMEWORKS["PMLA_2002"]]
            ))

        # ---------------------------------------------------------------------
        # RULE 7: RBI 2026 KYC Amendment Directions — Cross-Border / Non-Resident Checks
        # ---------------------------------------------------------------------
        is_cross_border = location in CROSS_BORDER_HIGH_RISK_JURISDICTIONS
        has_certified_copy = bool(row.get("has_overseas_certified_kyc", False))

        if is_cross_border and not has_certified_copy:
            triggered.append(RuleResult(
                rule_id="RULE_RBI_2026_KYC_CROSS_BORDER",
                rule_name="RBI 2026 Cross-Border KYC Verification Requirement",
                severity="CRITICAL",
                score_contribution=40.0,
                reason=(
                    f"Cross-border transfer routing through high-risk jurisdiction '{location}' "
                    f"requires certified copy of OVD / Aadhaar from authorized authorities "
                    f"(Embassy, Notary abroad, Magistrate, or overseas SCB branch) under RBI 2026 Directions."
                ),
                regulatory_references=[
                    REGULATORY_FRAMEWORKS["RBI_KYC_2026_COMMERCIAL"],
                    REGULATORY_FRAMEWORKS["RBI_KYC_2026_SFB"],
                    REGULATORY_FRAMEWORKS["FEMA_5R"],
                    REGULATORY_FRAMEWORKS["PML_RULES_2005"]
                ]
            ))

        # ---------------------------------------------------------------------
        # RULE 8: Cybersecurity Device Anomaly (CSAM / IAM Integrity)
        # ---------------------------------------------------------------------
        if "DEV_ANOM" in device_id or "UNKNOWN" in device_id:
            triggered.append(RuleResult(
                rule_id="RULE_CYBER_UNRECOGNIZED_DEVICE",
                rule_name="Unrecognized or Flagged Endpoint Device",
                severity="MEDIUM",
                score_contribution=15.0,
                reason=f"Transaction initiated from unverified hardware endpoint signature ({device_id}).",
                regulatory_references=["Cybersecurity Step 3 (Asset Management)", "Cybersecurity Step 6 (IAM)"]
            ))

        # Calculate normalized composite rule score (capped at 100.0)
        raw_score = sum(r.score_contribution for r in triggered)
        rule_score = min(100.0, raw_score)

        # Generate summary explanation
        if triggered:
            top_rule = max(triggered, key=lambda r: r.score_contribution)
            summary = f"Flagged by {len(triggered)} AML rules (Score: {rule_score:.0f}/100). Primary: {top_rule.rule_name} — {top_rule.reason}"
        else:
            summary = "No heuristic AML rules triggered. Transaction conforms to normal operational boundaries."

        return RuleEvaluation(
            rule_score=rule_score,
            triggered_count=len(triggered),
            triggered_rules=triggered,
            summary_explanation=summary
        )

    def evaluate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluates an entire DataFrame of transactions and appends rule detection columns.
        Returns a DataFrame containing ['rule_score', 'rule_triggered_count', 'rule_details', 'rule_explanation'].
        """
        logger.info("Evaluating rule engine against %d transactions...", len(df))
        scores = []
        counts = []
        explanations = []

        for _, row in df.iterrows():
            eval_res = self.evaluate_transaction(row)
            scores.append(eval_res.rule_score)
            counts.append(eval_res.triggered_count)
            explanations.append(eval_res.summary_explanation)

        df_out = df.copy()
        df_out["rule_score"] = scores
        df_out["rule_triggered_count"] = counts
        df_out["rule_explanation"] = explanations

        logger.info(
            "Rule evaluation complete. Triggered transactions: %d / %d (%.2f%%)",
            sum(1 for c in counts if c > 0),
            len(df),
            (sum(1 for c in counts if c > 0) / len(df) * 100) if len(df) > 0 else 0
        )
        return df_out
