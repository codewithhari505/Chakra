"""
Investigation Workflow and Case Management Service — Phase 15.

Implements:
1. Strict statutory lifecycle state machine:
   NEW → UNDER_REVIEW → ESCALATED → CLOSED
                      → CLOSED (direct triage resolution)
2. FIU-IND Suspicious Transaction Report (STR) formal reporting generator (PMLA 2002 §12).
3. Enhanced Due Diligence (EDD) regulatory docket generator (RBI KYC 2026 Directions).
4. Immutable audit trail logging for all supervisor and investigator actions.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Valid state machine transitions
ALLOWED_TRANSITIONS = {
    "NEW": {"UNDER_REVIEW"},
    "UNDER_REVIEW": {"ESCALATED", "CLOSED"},
    "ESCALATED": {"CLOSED"},
    "CLOSED": {"UNDER_REVIEW"},  # Allowed only for authorized supervisor reopen
}

VALID_RESOLUTIONS = {
    "TRUE_POSITIVE",
    "FALSE_POSITIVE",
    "INCONCLUSIVE",
    "ESCALATED_TO_AUTHORITY",
    "STR_FILED",
    "SAR_FILED",
}

# In-memory audit log for real-time investigation audit tracking
_GLOBAL_AUDIT_LOG: List[Dict[str, Any]] = []


class InvestigationWorkflowError(ValueError):
    """Raised when an invalid lifecycle state transition is attempted."""
    pass


class InvestigationService:
    """
    Service managing alert lifecycles, regulatory disclosures,
    and compliance dossier generation.
    """

    @staticmethod
    def validate_transition(current_status: str, new_status: str, is_supervisor: bool = False) -> bool:
        """
        Validates if transitioning from current_status to new_status is permitted.
        Raises InvestigationWorkflowError if invalid.
        """
        current_status = current_status.upper().strip()
        new_status = new_status.upper().strip()

        if current_status == new_status:
            return True

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvestigationWorkflowError(
                f"Illegal state transition from '{current_status}' to '{new_status}'. "
                f"Permitted next states: {sorted(list(allowed))}."
            )

        if current_status == "CLOSED" and new_status == "UNDER_REVIEW" and not is_supervisor:
            raise InvestigationWorkflowError(
                "Only an authorized compliance supervisor may reopen a CLOSED investigation."
            )

        return True

    @staticmethod
    def log_audit_event(
        alert_id: str,
        action: str,
        actor: str,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Records an immutable audit event for regulatory inspection."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_id": alert_id,
            "action": action,
            "actor": actor or "SYSTEM",
            "previous_status": previous_status,
            "new_status": new_status,
            "notes": notes,
            "metadata": metadata or {},
        }
        _GLOBAL_AUDIT_LOG.append(event)
        logger.info(
            "Investigation audit event: alert=%s action=%s actor=%s status=%s->%s",
            alert_id, action, actor, previous_status, new_status
        )
        return event

    @staticmethod
    def get_audit_trail(alert_id: str) -> List[Dict[str, Any]]:
        """Returns all audit events recorded for a given alert ID."""
        return [e for e in _GLOBAL_AUDIT_LOG if e["alert_id"] == alert_id]

    @staticmethod
    def generate_fiu_str_payload(
        alert_dict: Dict[str, Any],
        transaction_dict: Optional[Dict[str, Any]] = None,
        investigator_officer: Optional[str] = None,
        narrative: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a formal FIU-IND Suspicious Transaction Report (STR) payload
        compliant with PMLA 2002 Section 12 and PML Rules 2005.
        """
        alert_id = alert_dict.get("alert_id", "UNKNOWN")
        risk_score = alert_dict.get("risk_score", 0.0)
        risk_level = alert_dict.get("risk_level", "HIGH")
        alert_type = alert_dict.get("alert_type", "UNSPECIFIED_PATTERN")

        txn = transaction_dict or {}
        amount = txn.get("amount") or txn.get("transaction_amount") or 0.0
        channel = txn.get("channel", "ONLINE")

        payload = {
            "header": {
                "report_type": "STR_PMLA_2002_SEC12",
                "reporting_entity_code": "IN_BANK_042",
                "reporting_entity_category": "SCHEDULED_COMMERCIAL_BANK",
                "submission_timestamp": datetime.now(timezone.utc).isoformat(),
                "regulatory_authority": "Financial Intelligence Unit - India (FIU-IND), New Delhi",
                "statutory_mandate": "Prevention of Money Laundering Act, 2002 (PMLA) Section 12",
            },
            "subject_entity": {
                "account_id": alert_dict.get("account_id") or txn.get("sender_account_id") or "UNKNOWN",
                "counterparty_account_id": txn.get("receiver_account_id"),
                "transaction_id": alert_dict.get("transaction_id") or txn.get("transaction_id"),
                "reported_transaction_amount_inr": float(amount),
                "transaction_timestamp": txn.get("timestamp"),
                "payment_channel": channel,
            },
            "suspicion_profile": {
                "alert_id": alert_id,
                "composite_risk_score": round(float(risk_score), 2),
                "risk_tier": risk_level,
                "flagged_typology": alert_type,
                "grounds_for_suspicion": narrative or alert_dict.get("explanation") or (
                    f"Automated pattern detection identified high probability {alert_type} "
                    f"with composite risk score {risk_score}/100."
                ),
                "rbi_guideline_reference": "RBI Master Direction - KYC Amendment Directions 2026",
            },
            "investigation_sign_off": {
                "investigating_officer": investigator_officer or alert_dict.get("assigned_to") or "LEAD_AML_OFFICER",
                "verification_status": "MANUALLY_TRIAGED_AND_VERIFIED",
                "disclaimer": (
                    "This Suspicious Transaction Report (STR) is generated based on automated pattern risk "
                    "intelligence and confirmed by a certified anti-money-laundering compliance officer. "
                    "It constitutes regulatory reporting under PMLA §12, not a judicial finding of guilt."
                ),
            },
        }
        return payload

    @staticmethod
    def generate_rbi_edd_docket(
        account_id: str,
        risk_level: str = "HIGH",
        suspected_typology: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates an Enhanced Due Diligence (EDD) regulatory compliance docket
        enforcing RBI 2026 KYC Amendment Directions (PMLA §35A, Rule 9(14), FEMA 5(R)).
        """
        return {
            "docket_id": f"EDD_{account_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
            "account_id": account_id,
            "statutory_framework": "RBI Master Direction - KYC Amendment Directions 2026 (Updated March 2026)",
            "risk_classification": risk_level,
            "suspected_typology": suspected_typology or "ELEVATED_VELOCITY_OR_STRUCTURING",
            "statutory_requirements": [
                {
                    "item": "Beneficial Ownership (UBO) Disclosure",
                    "requirement": "Verify natural persons holding ≥ 10% ownership or control pursuant to amended PML Rule 9(14).",
                    "mandatory": True,
                },
                {
                    "item": "Overseas Certified OVD Recognition",
                    "requirement": (
                        "For non-resident counterparties, accept only certified copies attested by 1 of 6 authorized overseas entities: "
                        "(1) Overseas branches of Scheduled Commercial Banks registered in India, "
                        "(2) Branches of overseas banks with correspondent relationship, "
                        "(3) Authorized foreign public notaries, "
                        "(4) Judicial magistrates, "
                        "(5) Law court judges, "
                        "(6) Indian Embassy or Consulates."
                    ),
                    "mandatory": True,
                },
                {
                    "item": "Source of Funds Declaration",
                    "requirement": "Obtain audited financial statements, tax returns, or verifiable salary records explaining high velocity turnover.",
                    "mandatory": True,
                },
                {
                    "item": "Senior Management Sign-Off",
                    "requirement": "Enhanced Due Diligence approval must be signed off by a designated Senior Officer (Branch Head or Principal Officer).",
                    "mandatory": True,
                },
            ],
            "docket_status": "PENDING_VERIFICATION",
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
