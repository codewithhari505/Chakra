"""
SQLAlchemy ORM model for AML alerts and investigation cases.

Each alert is generated when a transaction or account pattern
triggers a suspicion threshold. Investigators work through these alerts.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Alert(Base):
    """
    Represents an AML alert raised by the detection pipeline.
    
    Alert lifecycle:
        NEW → UNDER_REVIEW → ESCALATED → CLOSED
                                       → CLOSED (without escalation)
    
    Alerts are created by the risk engine and resolved by investigators.
    An alert is a flag for investigation — not evidence of criminal activity.
    """

    __tablename__ = "alerts"

    # --- Primary Key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business identifier — format: ALT000001
    alert_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # --- Links ---
    transaction_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("transactions.transaction_id", ondelete="SET NULL"), nullable=True, index=True
    )
    account_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True, index=True
    )

    # --- Risk ---
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # LOW | MEDIUM | HIGH | CRITICAL

    # --- Detection Details ---
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. RAPID_TRANSFER | CIRCULAR_TRANSFER | LAYERING | STRUCTURING | ANOMALY | ML_FLAG

    detected_patterns: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: list of pattern objects with rule, reason fields

    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Human-readable explanation of why the alert was raised

    top_features: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: list of {feature, importance} dicts from SHAP / model

    # --- Investigation Workflow ---
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="NEW")
    # NEW | UNDER_REVIEW | ESCALATED | CLOSED

    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Investigator username (future auth integration)

    investigation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Investigator notes added during review

    resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # TRUE_POSITIVE | FALSE_POSITIVE | INCONCLUSIVE | ESCALATED_TO_AUTHORITY

    # --- Audit ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    transaction: Mapped["Transaction | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Transaction", back_populates="alert"
    )
    account: Mapped["Account | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Account", back_populates="alerts"
    )

    __table_args__ = (
        Index("ix_alert_status", "status"),
        Index("ix_alert_risk_level", "risk_level"),
        Index("ix_alert_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Alert {self.alert_id} type={self.alert_type} status={self.status}>"
