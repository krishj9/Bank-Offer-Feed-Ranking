"""Feedback API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_request_context, log_event
from app.schemas.feedback import (
    FeedbackEventRequest,
    FeedbackEventResponse,
    ProductMetricsReportResponse,
    ProductMetricsSummary,
)
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/api/v1", tags=["feedback"])
LOGGER = logging.getLogger(__name__)


@router.post(
    "/feedback",
    response_model=FeedbackEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_feedback(payload: FeedbackEventRequest) -> FeedbackEventResponse:
    """Persist a feedback event for later analytics/retraining."""
    request_id, correlation_id = get_request_context()
    resolved_request_id = payload.request_id or request_id
    log_event(
        LOGGER,
        "feedback request received",
        event_type="feedback_request_received",
        request_id=resolved_request_id,
        correlation_id=correlation_id,
        model_version=payload.model_version or "unknown",
        feature_version=payload.feature_version or "unknown",
    )
    try:
        persisted = FeedbackService().persist(payload)
    except OSError as exc:
        log_event(
            LOGGER,
            "feedback persistence failed",
            event_type="feedback_persist_failed",
            request_id=resolved_request_id,
            correlation_id=correlation_id,
            model_version=payload.model_version or "unknown",
            feature_version=payload.feature_version or "unknown",
            level=logging.ERROR,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist feedback: {exc}",
        ) from exc

    log_event(
        LOGGER,
        "feedback response returned",
        event_type="feedback_response_returned",
        request_id=resolved_request_id,
        correlation_id=correlation_id,
        model_version=payload.model_version or "unknown",
        feature_version=payload.feature_version or "unknown",
    )
    return FeedbackEventResponse(
        event_id=persisted.event_id,
        status="stored",
        stored_at=persisted.stored_at,
        storage=persisted.storage,
    )


@router.get(
    "/feedback/metrics",
    response_model=ProductMetricsReportResponse,
    status_code=status.HTTP_200_OK,
)
def feedback_metrics_report() -> ProductMetricsReportResponse:
    """Return aggregated product metrics from stored feedback/impression events."""
    report = FeedbackService().generate_metrics_report()
    return ProductMetricsReportResponse(
        generated_at=report.generated_at,
        storage=report.storage,
        summary=ProductMetricsSummary(**report.summary),
        action_counts=report.action_counts,
    )
