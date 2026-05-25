"""Request schemas for ranking APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings
from app.schemas.sample_users import SampleUserProfile


class RankRequest(BaseModel):
    """Schema for rank request payload."""

    model_config = ConfigDict(extra="forbid")

    user_id: str | None = Field(default=None, min_length=1)
    user_profile: SampleUserProfile | None = None
    top_k: int = Field(default=settings.default_top_k, ge=1, le=settings.max_top_k)
    context: dict[str, Any] | None = None
    debug: bool = False

    @model_validator(mode="after")
    def validate_user_input(self) -> "RankRequest":
        """Require either a user identifier or an inline profile."""
        if not self.user_id and not self.user_profile:
            msg = "Either user_id or user_profile must be provided."
            raise ValueError(msg)
        return self
