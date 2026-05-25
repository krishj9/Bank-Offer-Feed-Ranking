"""Feedback persistence service."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_request_context, log_event
from app.schemas.feedback import FeedbackEventRequest

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProductMetricsReport:
    """Aggregated product metrics computed from stored events."""

    generated_at: datetime
    storage: str
    summary: dict[str, int]
    action_counts: dict[str, int]


@dataclass(frozen=True)
class PersistedFeedback:
    """Feedback persistence result."""

    event_id: str
    stored_at: datetime
    storage: str


class FeedbackService:
    """Persist feedback events to local JSONL storage."""

    def __init__(self, store_path: Path | None = None) -> None:
        configured_path = os.getenv("FEEDBACK_STORE_PATH", settings.feedback_store_path)
        self._store_path = store_path or settings.resolve_path(configured_path)

    def persist(self, event: FeedbackEventRequest) -> PersistedFeedback:
        """Persist one feedback event and return metadata."""
        stored_at = datetime.now(UTC)
        event_id = uuid4().hex
        _, context_correlation_id = get_request_context()
        correlation_id = event.correlation_id or context_correlation_id
        payload = {
            "event_id": event_id,
            "event_type": "feedback",
            "request_id": event.request_id,
            "correlation_id": correlation_id,
            "user_id": event.user_id,
            "offer_id": event.offer_id,
            "action_type": event.action_type.value,
            "model_version": event.model_version,
            "feature_version": event.feature_version,
            "score": event.score,
            "rank_position": event.rank_position,
            "timestamp": (event.timestamp or stored_at).isoformat(),
            "stored_at": stored_at.isoformat(),
        }

        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        with self._store_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=True) + "\n")

        log_event(
            LOGGER,
            "feedback persisted",
            event_type="feedback_persisted",
            request_id=event.request_id,
            correlation_id=correlation_id,
            model_version=event.model_version or "unknown",
            feature_version=event.feature_version or "unknown",
            action_type=event.action_type.value,
            offer_id=event.offer_id,
        )

        return PersistedFeedback(
            event_id=event_id,
            stored_at=stored_at,
            storage="jsonl",
        )

    def persist_impressions(
        self,
        *,
        request_id: str,
        user_id: str,
        offer_ids: list[str],
        model_version: str,
        feature_version: str,
        correlation_id: str | None = None,
    ) -> int:
        """Persist impression events for ranked offers shown to user."""
        if not offer_ids:
            return 0

        _, context_correlation_id = get_request_context()
        resolved_correlation_id = correlation_id or context_correlation_id
        stored_at = datetime.now(UTC)
        rows = []
        for rank, offer_id in enumerate(offer_ids, start=1):
            rows.append(
                {
                    "event_id": uuid4().hex,
                    "event_type": "impression",
                    "request_id": request_id,
                    "correlation_id": resolved_correlation_id,
                    "user_id": user_id,
                    "offer_id": offer_id,
                    "action_type": "viewed",
                    "model_version": model_version,
                    "feature_version": feature_version,
                    "score": None,
                    "rank_position": rank,
                    "timestamp": stored_at.isoformat(),
                    "stored_at": stored_at.isoformat(),
                }
            )

        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        with self._store_path.open("a", encoding="utf-8") as file:
            for row in rows:
                file.write(json.dumps(row, ensure_ascii=True) + "\n")

        log_event(
            LOGGER,
            "impressions persisted",
            event_type="impressions_persisted",
            request_id=request_id,
            correlation_id=resolved_correlation_id,
            model_version=model_version,
            feature_version=feature_version,
            impression_count=len(rows),
        )
        return len(rows)

    def generate_metrics_report(self) -> ProductMetricsReport:
        """Compute product metrics from stored JSONL events."""
        generated_at = datetime.now(UTC)
        if not self._store_path.exists():
            summary = {
                "impressions": 0,
                "feedback_events": 0,
                "accept_proxy_events": 0,
                "dismiss_proxy_events": 0,
                "total_events": 0,
            }
            return ProductMetricsReport(
                generated_at=generated_at,
                storage="jsonl",
                summary=summary,
                action_counts={},
            )

        action_counts: dict[str, int] = {}
        impressions = 0
        feedback_events = 0
        accept_proxy_events = 0
        dismiss_proxy_events = 0
        total_events = 0
        accept_actions = {"accepted", "clicked"}
        dismiss_actions = {"dismissed", "not_interested"}

        with self._store_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped:
                    continue
                total_events += 1
                row: dict[str, Any] = json.loads(stripped)
                action = str(row.get("action_type", "unknown"))
                event_type = str(row.get("event_type", "feedback"))
                action_counts[action] = action_counts.get(action, 0) + 1
                if event_type == "impression" or action == "viewed":
                    impressions += 1
                if event_type == "feedback":
                    feedback_events += 1
                if action in accept_actions:
                    accept_proxy_events += 1
                if action in dismiss_actions:
                    dismiss_proxy_events += 1

        summary = {
            "impressions": impressions,
            "feedback_events": feedback_events,
            "accept_proxy_events": accept_proxy_events,
            "dismiss_proxy_events": dismiss_proxy_events,
            "total_events": total_events,
        }
        log_event(
            LOGGER,
            "product metrics generated",
            event_type="product_metrics_generated",
            model_version="aggregate",
            feature_version="aggregate",
            impressions=impressions,
            feedback_events=feedback_events,
            accept_proxy_events=accept_proxy_events,
            dismiss_proxy_events=dismiss_proxy_events,
            total_events=total_events,
        )
        return ProductMetricsReport(
            generated_at=generated_at,
            storage="jsonl",
            summary=summary,
            action_counts=action_counts,
        )
