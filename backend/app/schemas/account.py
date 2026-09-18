"""
Pydantic schemas for Account API request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AccountBase(BaseModel):
    account_id: str = Field(..., description="Unique account identifier, e.g. ACC1023")
    account_type: str = Field("INDIVIDUAL", description="INDIVIDUAL | CORPORATE | SHELL | OFFSHORE")
    country: Optional[str] = None
    city: Optional[str] = None
    registration_date: Optional[datetime] = None


class AccountCreate(AccountBase):
    """Schema for creating a new account record."""
    pass


class AccountBehavioralStats(BaseModel):
    """Pre-aggregated behavioral statistics for an account."""
    total_transactions: int = 0
    total_inflow: Decimal = Decimal("0")
    total_outflow: Decimal = Decimal("0")
    average_transaction: Optional[float] = None
    max_transaction: Optional[Decimal] = None
    unique_senders: int = 0
    unique_receivers: int = 0


class AccountNetworkStats(BaseModel):
    """Graph/network statistics for an account."""
    degree: int = 0
    in_degree: int = 0
    out_degree: int = 0
    betweenness_centrality: Optional[float] = None
    pagerank: Optional[float] = None
    cycle_count: int = 0


class AccountResponse(AccountBase):
    """Schema returned by the API for a single account."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    is_flagged: bool
    behavioral: Optional[AccountBehavioralStats] = None
    network: Optional[AccountNetworkStats] = None
    created_at: datetime
    updated_at: datetime


class AccountListResponse(BaseModel):
    """Paginated list of accounts."""
    total: int
    page: int
    page_size: int
    items: list[AccountResponse]
