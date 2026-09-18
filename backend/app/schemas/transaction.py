"""
Pydantic schemas for Transaction API request/response validation.

Schemas are separate from ORM models:
- ORM models define database structure
- Schemas define API contract (what goes in, what comes out)
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionBase(BaseModel):
    """Fields common to all transaction schemas."""

    transaction_id: str = Field(..., description="Unique transaction identifier, e.g. TX000001")
    sender_account_id: Optional[str] = Field(None, description="Sender account ID")
    receiver_account_id: Optional[str] = Field(None, description="Receiver account ID")
    amount: Decimal = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field("INR", max_length=10, description="ISO 4217 currency code")
    transaction_type: str = Field(..., description="TRANSFER | DEPOSIT | WITHDRAWAL | PAYMENT | ATM")
    timestamp: datetime = Field(..., description="Transaction timestamp (UTC)")
    location: Optional[str] = Field(None, description="Geographic location")
    channel: Optional[str] = Field(None, description="ONLINE | MOBILE | ATM | BRANCH | POS")
    device_id: Optional[str] = Field(None, description="Device identifier")
    merchant_category: Optional[str] = Field(None, description="Merchant category code")


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction record."""

    is_suspicious: bool = Field(False, description="Ground-truth label (synthetic data only)")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"TRANSFER", "DEPOSIT", "WITHDRAWAL", "PAYMENT", "ATM"}
        v = v.upper().strip()
        if v not in allowed:
            raise ValueError(f"transaction_type must be one of {allowed}")
        return v


class TransactionRiskResult(BaseModel):
    """Risk analysis result attached to a transaction response."""

    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = None
    ml_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    rule_score: Optional[float] = None
    network_score: Optional[float] = None
    detected_patterns: Optional[list[dict[str, Any]]] = None


class TransactionResponse(TransactionBase):
    """Schema returned by the API for a single transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_suspicious: bool
    risk: Optional[TransactionRiskResult] = None
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    total: int
    page: int
    page_size: int
    items: list[TransactionResponse]


class TransactionAnalyzeRequest(BaseModel):
    """Request body for the POST /transactions/analyze endpoint."""

    transaction: TransactionCreate
    include_graph: bool = Field(False, description="Include graph analysis in response")
    include_explanation: bool = Field(True, description="Include rule/feature explanations")
