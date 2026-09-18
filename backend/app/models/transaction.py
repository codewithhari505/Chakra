"""
SQLAlchemy ORM model for financial transactions.

This table is the core of the AML system.
Each row represents a single financial transaction between two accounts.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Transaction(Base):
    """
    Represents a financial transaction in the AML system.
    
    Columns are intentionally broad to accommodate different transaction types
    (wire transfers, card payments, ATM, etc.) without requiring separate tables.
    """

    __tablename__ = "transactions"

    # --- Primary Key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business identifier — format: TX000001
    transaction_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # --- Parties ---
    sender_account_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True, index=True
    )
    receiver_account_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True, index=True
    )

    # --- Transaction Details ---
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. TRANSFER, DEPOSIT, WITHDRAWAL, PAYMENT, ATM

    # --- Context ---
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # e.g. ONLINE, MOBILE, ATM, BRANCH, POS

    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    merchant_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- Labels ---
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Ground truth label (in synthetic data) — NOT a legal determination

    # --- Risk / ML Outputs (populated after analysis) ---
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # LOW | MEDIUM | HIGH | CRITICAL

    ml_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rule_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    network_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Detected Patterns (JSON string) ---
    detected_patterns: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Stored as JSON — deserialize in the schema/service layer

    # --- Audit ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relationships ---
    sender: Mapped["Account"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Account", foreign_keys=[sender_account_id], back_populates="sent_transactions"
    )
    receiver: Mapped["Account"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Account", foreign_keys=[receiver_account_id], back_populates="received_transactions"
    )
    alert: Mapped["Alert | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Alert", back_populates="transaction", uselist=False
    )

    # --- Indexes for common query patterns ---
    __table_args__ = (
        Index("ix_txn_sender_timestamp", "sender_account_id", "timestamp"),
        Index("ix_txn_receiver_timestamp", "receiver_account_id", "timestamp"),
        Index("ix_txn_risk_level", "risk_level"),
        Index("ix_txn_suspicious", "is_suspicious"),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_id} amount={self.amount} {self.currency}>"
