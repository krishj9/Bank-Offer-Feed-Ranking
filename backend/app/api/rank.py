"""Ranking and sample-user API routes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_request_context, log_event
from app.schemas.request import RankRequest
from app.schemas.response import RankResponse
from app.schemas.sample_users import SampleUsersResponse
from app.services.feedback_service import FeedbackService
from app.services.candidate_service import (
    CandidateService,
    CandidateServiceError,
    NoEligibleOffersError,
    UserNotFoundError,
)
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/api/v1", tags=["ranking"])
LOGGER = logging.getLogger(__name__)

_candidate_service = CandidateService()
_ranking_service = RankingService()


@router.post("/rank", response_model=RankResponse, status_code=status.HTTP_200_OK)
def rank_offers(payload: RankRequest) -> RankResponse:
    """Rank offers for a user and return top-K results."""
    request_id, correlation_id = get_request_context()
    log_event(
        LOGGER,
        "rank request received",
        event_type="rank_request_received",
        request_id=request_id,
        correlation_id=correlation_id,
    )
    try:
        user_profile = _candidate_service.resolve_user_profile(
            user_id=payload.user_id,
            inline_profile=payload.user_profile,
        )
        candidates = _candidate_service.build_candidates(user_profile)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NoEligibleOffersError:
        fallback_request_id = request_id or payload.user_id or (
            payload.user_profile.user_id if payload.user_profile else "unknown"
        )
        model_version = "fallback-v1"
        feature_version = "feature-default-v1"
        log_event(
            LOGGER,
            "rank request has no eligible offers",
            event_type="rank_no_eligible_offers",
            request_id=fallback_request_id,
            correlation_id=correlation_id,
            model_version=model_version,
            feature_version=feature_version,
        )
        return RankResponse(
            request_id=fallback_request_id,
            model_version=model_version,
            feature_version=feature_version,
            generated_at=datetime.now(UTC),
            results=[],
            warnings=["No eligible offers for this user profile."],
        )
    except CandidateServiceError as exc:
        log_event(
            LOGGER,
            "candidate service failed",
            event_type="rank_candidate_error",
            request_id=request_id,
            correlation_id=correlation_id,
            level=logging.ERROR,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    response = _ranking_service.rank_candidates(
        user_profile=user_profile.model_dump(),
        candidates=candidates,
        top_k=payload.top_k,
        request_id=request_id,
    )
    FeedbackService().persist_impressions(
        request_id=response.request_id,
        user_id=user_profile.user_id,
        offer_ids=[item.offer_id for item in response.results],
        model_version=response.model_version,
        feature_version=response.feature_version,
        correlation_id=correlation_id,
    )
    log_event(
        LOGGER,
        "rank response returned",
        event_type="rank_response_returned",
        request_id=response.request_id,
        correlation_id=correlation_id,
        model_version=response.model_version,
        feature_version=response.feature_version,
        results_count=len(response.results),
    )
    return response


@router.get(
    "/sample-users",
    response_model=SampleUsersResponse,
    status_code=status.HTTP_200_OK,
)
def sample_users() -> SampleUsersResponse:
    """Return sample users available for demo rank requests."""
    try:
        users = _candidate_service.list_sample_users()
    except CandidateServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return SampleUsersResponse(users=users, count=len(users))
