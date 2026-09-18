"""
Pydantic schemas for Alert API request/response validation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


VALID_STATUSES = {"NEW", "UNDER_REVIEW", "ESCALATED", "CLOSED"}
VALID_RESOLUTIONS = {"TRUE_POSITIVE", "FALSE_POSITIVE", "INCONCLUSIVE", "ESCALATED_TO_AUTHORITY"}


class AlertBase(BaseModel):
    alert_id: str
    transaction_id: Optional[str] = None
    account_id: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = None
    alert_type: str
    detected_patterns: Optional[list[dict[str, Any]]] = None
    explanation: Optional[str] = None


class AlertResponse(AlertBase):
    """Schema returned by the API for a single alert."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None
    resolution: Optional[str] = None
    top_features: Optional[list[dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""
    total: int
    page: int
    page_size: int
    items: list[AlertResponse]


class AlertUpdateRequest(BaseModel):
    """Body for updating alert status during investigation."""

    status: Optional[str] = Field(None, description="NEW | UNDER_REVIEW | ESCALATED | CLOSED")
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None
    resolution: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.status and self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        if self.resolution and self.resolution not in VALID_RESOLUTIONS:
            raise ValueError(f"resolution must be one of {VALID_RESOLUTIONS}")
