"""Response schemas for ranking APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class RankedOffer(BaseModel):
    """Single ranked offer in ranking response."""

    model_config = ConfigDict(extra="forbid")

    rank: int
    offer_id: str
    offer_type: str
    title: str
    model_score: float
    normalized_score: float
    explanation: str
    model_version: str
    request_id: str
    rerank_factors: dict[str, Any]


class RankResponse(BaseModel):
    """Top-level response for rank API."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    model_version: str
    feature_version: str
    generated_at: datetime
    results: list[RankedOffer]
    warnings: list[str] = []
