"""Schemas for sample user payloads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SampleUserProfile(BaseModel):
    """Sample user profile used by ranking endpoints."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    age: int
    job: str
    marital: str
    education: str
    default: str
    housing: str
    loan: str
    contact: str
    month: str
    day_of_week: str
    campaign: int
    pdays: int
    previous: int
    poutcome: str
    emp_var_rate: float
    cons_price_idx: float
    cons_conf_idx: float
    euribor3m: float
    nr_employed: float


class SampleUsersResponse(BaseModel):
    """List of demo users for frontend selector."""

    users: list[SampleUserProfile]
    count: int
