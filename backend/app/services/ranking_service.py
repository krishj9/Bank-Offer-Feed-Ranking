"""Ranking orchestration service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pandas as pd

from app.core.config import settings
from app.core.logging import get_request_context, log_event
from app.core.model_loader import ModelArtifactLoader
from app.schemas.response import RankResponse, RankedOffer
from app.services.candidate_service import CandidateOffer
from app.services.explanation_service import ExplanationService
from app.services.rerank_service import RerankService
from ml.features.builder import FeatureBuilder


class RankingService:
    """Build features, score candidates, rerank, and format response."""

    def __init__(
        self,
        rerank_service: RerankService | None = None,
        explanation_service: ExplanationService | None = None,
    ) -> None:
        self._artifact_loader = ModelArtifactLoader()
        self._feature_builder = FeatureBuilder(
            settings.resolve_path(settings.feature_schema_path)
        )
        self._rerank_service = rerank_service or RerankService()
        self._explanation_service = explanation_service or ExplanationService()

    def rank_candidates(
        self,
        *,
        user_profile: dict[str, Any],
        candidates: list[CandidateOffer],
        top_k: int,
        request_id: str | None = None,
    ) -> RankResponse:
        """Rank candidate offers and return API response model."""
        resolved_request_id = request_id or uuid4().hex
        _, correlation_id = get_request_context()
        artifact_bundle = self._artifact_loader.load()
        warnings: list[str] = []

        if not artifact_bundle.ready:
            warnings.append(
                "Model artifacts unavailable; serving deterministic fallback scores."
            )

        rows = [candidate.feature_payload for candidate in candidates]
        feature_df = pd.DataFrame(rows)
        built_features = self._feature_builder.build_features(feature_df, is_training=False)

        model_scores = self._score_rows(
            built_features=built_features,
            raw_rows=rows,
            loaded_model=artifact_bundle.model,
            ready=artifact_bundle.ready,
        )
        normalized_scores = self._normalize_scores(model_scores)

        scored_rows: list[dict[str, Any]] = []
        for index, (candidate, score, normalized) in enumerate(
            zip(candidates, model_scores, normalized_scores, strict=True),
            start=1,
        ):
            scored_rows.append(
                {
                    "raw_rank": index,
                    "offer": candidate.offer,
                    "model_score": score,
                    "normalized_score": normalized,
                    "candidate": candidate,
                    "rerank_factors": {},
                }
            )

        pre_rerank = sorted(
            scored_rows,
            key=lambda row: (
                -row["normalized_score"],
                -row["model_score"],
                row["offer"]["offer_id"],
            ),
        )
        for index, row in enumerate(pre_rerank, start=1):
            row["raw_rank"] = index

        reranked = self._rerank_service.rerank(pre_rerank)
        top_ranked = reranked[:top_k]

        results: list[RankedOffer] = []
        model_version = self._resolve_model_version(artifact_bundle.manifest)
        feature_version = self._resolve_feature_version(artifact_bundle.preprocessor)
        log_event(
            logging.getLogger(__name__),
            "ranking candidates scored",
            event_type="ranking_scored",
            request_id=resolved_request_id,
            correlation_id=correlation_id,
            model_version=model_version,
            feature_version=feature_version,
            candidate_count=len(candidates),
            top_k=top_k,
        )
        for index, row in enumerate(top_ranked, start=1):
            offer = row["offer"]
            explanation = self._explanation_service.safe_generate(
                user_profile=user_profile,
                offer=offer,
            )
            results.append(
                RankedOffer(
                    rank=index,
                    offer_id=offer["offer_id"],
                    offer_type=offer["offer_type"],
                    title=offer["title"],
                    model_score=row["model_score"],
                    normalized_score=row["normalized_score"],
                    explanation=explanation,
                    model_version=model_version,
                    request_id=resolved_request_id,
                    rerank_factors=row["rerank_factors"],
                )
            )

        return RankResponse(
            request_id=resolved_request_id,
            model_version=model_version,
            feature_version=feature_version,
            generated_at=datetime.now(UTC),
            results=results,
            warnings=warnings,
        )

    def _score_rows(
        self,
        *,
        built_features: pd.DataFrame,
        raw_rows: list[dict[str, Any]],
        loaded_model: Any,
        ready: bool,
    ) -> list[float]:
        if ready and loaded_model is not None:
            return self._model_scores(loaded_model, built_features)
        return [self._fallback_score(row) for row in raw_rows]

    def _model_scores(self, model: Any, feature_df: pd.DataFrame) -> list[float]:
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(feature_df)
            if getattr(probabilities, "ndim", 0) == 2 and probabilities.shape[1] > 1:
                return [float(p[1]) for p in probabilities]
            return [float(p[0]) for p in probabilities]
        if hasattr(model, "decision_function"):
            decisions = model.decision_function(feature_df)
            return [float(value) for value in decisions]
        predictions = model.predict(feature_df)
        return [float(value) for value in predictions]

    def _fallback_score(self, row: dict[str, Any]) -> float:
        affinity = float(row.get("affinity_score", 0.5))
        priority = float(row.get("priority_weight", 1.0))
        campaign = float(row.get("campaign", 0))
        previous = float(row.get("previous", 0))
        score = affinity + (priority * 0.2) + min(campaign, 5.0) * 0.03 + min(previous, 3.0) * 0.05
        return max(0.0, min(score, 2.0))

    def _normalize_scores(self, scores: list[float]) -> list[float]:
        if not scores:
            return []
        score_min = min(scores)
        score_max = max(scores)
        if score_max == score_min:
            return [1.0 for _ in scores]
        return [(value - score_min) / (score_max - score_min) for value in scores]

    def _resolve_model_version(self, manifest: dict[str, Any] | None) -> str:
        if manifest and manifest.get("run_id"):
            return str(manifest["run_id"])
        return "fallback-v1"

    def _resolve_feature_version(self, preprocessor: dict[str, Any] | None) -> str:
        if preprocessor and preprocessor.get("feature_version"):
            return str(preprocessor["feature_version"])
        return "feature-default-v1"
