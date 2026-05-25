"""Deterministic explanation generation."""

from __future__ import annotations

from typing import Any


class ExplanationService:
    """Create deterministic offer explanations with graceful fallback."""

    _TEMPLATES = {
        "term_deposit_reminder": (
            "Ranked highly because this profile aligns with long-term savings preferences."
        ),
        "savings_boost": (
            "Ranked highly because this profile matches short-term savings growth criteria."
        ),
        "credit_card_upgrade": (
            "Ranked highly because this profile suggests strong eligibility for credit upgrades."
        ),
        "refinance_prompt": (
            "Ranked highly because this profile indicates potential value from loan refinancing."
        ),
        "advisor_callback": (
            "Ranked highly because this profile benefits from personalized financial guidance."
        ),
    }

    _FALLBACK = (
        "Ranked using available profile and offer-match signals; detailed explanation unavailable."
    )

    def generate(self, *, user_profile: dict[str, Any], offer: dict[str, Any]) -> str:
        """Generate deterministic explanation text."""
        offer_type = str(offer.get("offer_type", "")).strip()
        template = self._TEMPLATES.get(offer_type)
        if template:
            return template

        # Generic deterministic explanation for unknown offer types.
        loan_state = user_profile.get("loan", "unknown")
        return (
            "Ranked based on profile compatibility and business priorities "
            f"(loan status: {loan_state})."
        )

    def safe_generate(self, *, user_profile: dict[str, Any], offer: dict[str, Any]) -> str:
        """Always return explanation text even if generation fails."""
        try:
            return self.generate(user_profile=user_profile, offer=offer)
        except Exception:  # noqa: BLE001 - fallback on explanation failure by design.
            return self._FALLBACK
