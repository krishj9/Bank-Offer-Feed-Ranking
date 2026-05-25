"""Candidate generation service for user-offer pairs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.sample_users import SampleUserProfile
from ml.data.eligibility import check_eligibility


class CandidateServiceError(Exception):
    """Base candidate generation error."""


class UserNotFoundError(CandidateServiceError):
    """Raised when requested user id does not exist in sample users."""


class NoEligibleOffersError(CandidateServiceError):
    """Raised when no eligible offers were found for the user."""


@dataclass(frozen=True)
class CandidateOffer:
    """Offer and feature payload for scoring."""

    offer: dict[str, Any]
    feature_payload: dict[str, Any]
    eligibility_reasons: list[str]


class CandidateService:
    """Build eligible offer candidates for ranking."""

    def __init__(
        self,
        sample_users_path: Path | None = None,
        offers_path: Path | None = None,
    ) -> None:
        self._sample_users_path = sample_users_path or settings.resolve_path(
            settings.sample_users_path
        )
        self._offers_path = offers_path or settings.resolve_path(settings.offers_path)

    def list_sample_users(self) -> list[SampleUserProfile]:
        """Return all sample users from processed artifact."""
        payload = self._read_json(self._sample_users_path)
        if not isinstance(payload, list):
            raise CandidateServiceError("Sample users payload must be a list.")
        return [SampleUserProfile.model_validate(user) for user in payload]

    def resolve_user_profile(
        self,
        *,
        user_id: str | None,
        inline_profile: SampleUserProfile | None,
    ) -> SampleUserProfile:
        """Resolve user profile from inline payload or sample-user lookup."""
        if inline_profile is not None:
            return inline_profile
        if not user_id:
            raise CandidateServiceError("Either user_id or inline profile is required.")

        for user in self.list_sample_users():
            if user.user_id == user_id:
                return user

        raise UserNotFoundError(f"Unknown sample user_id: {user_id}")

    def build_candidates(self, user_profile: SampleUserProfile) -> list[CandidateOffer]:
        """Build eligible candidate offers for scoring."""
        offers = self._load_offers()
        user_dict = user_profile.model_dump()
        candidates: list[CandidateOffer] = []

        for offer in offers:
            if not offer.get("active", False):
                continue
            is_eligible, reasons = check_eligibility(user_dict, offer)
            if not is_eligible:
                continue

            affinity_score = self._compute_affinity(user_dict, offer)
            feature_payload = {
                **user_dict,
                "offer_id": offer["offer_id"],
                "offer_type": offer["offer_type"],
                "category": offer["category"],
                "priority_weight": float(offer["priority_weight"]),
                "is_eligible": True,
                "affinity_score": affinity_score,
            }
            # Explicitly guarantee leakage feature is never passed downstream.
            feature_payload.pop("duration", None)

            candidates.append(
                CandidateOffer(
                    offer=offer,
                    feature_payload=feature_payload,
                    eligibility_reasons=reasons,
                )
            )

        if not candidates:
            raise NoEligibleOffersError(
                f"No eligible offers available for user {user_profile.user_id}."
            )

        return candidates

    def _read_json(self, path: Path) -> Any:
        if not path.exists():
            raise CandidateServiceError(f"Missing artifact file: {path}")
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise CandidateServiceError(f"Failed to read JSON artifact: {exc}") from exc

    def _load_offers(self) -> list[dict[str, Any]]:
        """Load offers CSV and deserialize eligibility rules."""
        if not self._offers_path.exists():
            raise CandidateServiceError(f"Missing offers artifact: {self._offers_path}")

        offers: list[dict[str, Any]] = []
        try:
            with self._offers_path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    eligibility_rules = json.loads(row.get("eligibility_rules", "{}"))
                    offers.append(
                        {
                            "offer_id": row["offer_id"],
                            "offer_type": row["offer_type"],
                            "title": row["title"],
                            "description": row.get("description", ""),
                            "category": row["category"],
                            "priority_weight": float(row.get("priority_weight", 1.0)),
                            "active": str(row.get("active", "true")).lower() == "true",
                            "eligibility_rules": eligibility_rules,
                            "version": row.get("version", "1.0"),
                        }
                    )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise CandidateServiceError(f"Failed to load offers artifact: {exc}") from exc

        return offers

    def _compute_affinity(self, user: dict[str, Any], offer: dict[str, Any]) -> float:
        """Deterministic heuristic affinity used in fallback scoring."""
        score = 0.5
        offer_type = str(offer.get("offer_type", ""))
        if offer_type in {"savings_boost", "term_deposit_reminder"}:
            score += 0.2 if user.get("housing") == "yes" else 0.05
        if offer_type in {"credit_card_upgrade", "refinance_prompt"}:
            score += 0.2 if user.get("education") in {"university.degree", "professional.course"} else 0.0
            score += 0.1 if user.get("loan") == "yes" else 0.0
        if offer_type == "advisor_callback":
            score += 0.15 if int(user.get("age", 0)) >= 40 else 0.0
            score += 0.1 if int(user.get("previous", 0)) > 0 else 0.0

        score += min(int(user.get("campaign", 0)), 10) * 0.01
        return max(0.0, min(score, 1.0))
