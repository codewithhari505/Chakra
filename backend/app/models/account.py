"""
SQLAlchemy ORM model for financial accounts.

Accounts are the nodes in the transaction graph.
Behavioral statistics are pre-aggregated here for fast risk lookup.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Account(Base):
    """
    Represents a financial account in the AML system.
    
    Aggregated behavioral statistics are stored as pre-computed columns
    so the API can return them quickly without re-scanning all transactions.
    These are updated by the ML pipeline or a periodic background job.
    """

    __tablename__ = "accounts"

    # --- Primary Key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business identifier — format: ACC1023
    account_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # --- Profile ---
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, default="INDIVIDUAL")
    # INDIVIDUAL | CORPORATE | SHELL | OFFSHORE | UNKNOWN

    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registration_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Risk ---
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Behavioral Statistics (updated by ML pipeline) ---
    total_transactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_inflow: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), default=0, nullable=False)
    total_outflow: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), default=0, nullable=False)
    average_transaction: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_transaction: Mapped[Decimal | None] = mapped_column(Numeric(precision=18, scale=2), nullable=True)
    unique_senders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_receivers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # --- Network Statistics ---
    degree: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    in_degree: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    out_degree: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    betweenness_centrality: Mapped[float | None] = mapped_column(Float, nullable=True)
    pagerank: Mapped[float | None] = mapped_column(Float, nullable=True)
    cycle_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # --- Detected Patterns ---
    detected_patterns: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Audit ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relationships ---
    sent_transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Transaction", foreign_keys="Transaction.sender_account_id", back_populates="sender"
    )
    received_transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Transaction", foreign_keys="Transaction.receiver_account_id", back_populates="receiver"
    )
    alerts: Mapped[list["Alert"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Alert", back_populates="account"
    )

    __table_args__ = (
        Index("ix_account_risk_level", "risk_level"),
        Index("ix_account_flagged", "is_flagged"),
    )

    def __repr__(self) -> str:
        return f"<Account {self.account_id} risk={self.risk_level}>"
