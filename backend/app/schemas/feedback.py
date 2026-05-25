"""Schemas for feedback capture endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FeedbackAction(str, Enum):
    """Allowed feedback actions."""

    viewed = "viewed"
    clicked = "clicked"
    accepted = "accepted"
    dismissed = "dismissed"
    not_interested = "not_interested"


class FeedbackEventRequest(BaseModel):
    """Request payload for feedback endpoint."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    correlation_id: str | None = Field(default=None, min_length=1)
    user_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    action_type: FeedbackAction
    model_version: str | None = None
    feature_version: str | None = None
    score: float | None = None
    rank_position: int | None = Field(default=None, ge=1)
    timestamp: datetime | None = None


class FeedbackEventResponse(BaseModel):
    """Response payload for feedback endpoint."""

    event_id: str
    status: str
    stored_at: datetime
    storage: str


class ProductMetricsSummary(BaseModel):
    """Aggregated product metrics from stored events."""

    impressions: int
    feedback_events: int
    accept_proxy_events: int
    dismiss_proxy_events: int
    total_events: int


class ProductMetricsReportResponse(BaseModel):
    """Response payload for product metrics report endpoint."""

    generated_at: datetime
    storage: str
    summary: ProductMetricsSummary
    action_counts: dict[str, int]
