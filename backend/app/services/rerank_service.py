"""Reranking service for diversity and business rules."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class RerankConfig:
    """Runtime configuration for reranking behavior."""

    max_per_offer_type: int = 2
    priority_boost_enabled: bool = True
    priority_boost_weight: float = 0.05


class RerankService:
    """Apply diversity, deduplication, and deterministic ordering."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or settings.resolve_path(settings.rerank_config_path)
        self._config = self._load_config(self._config_path)

    def rerank(self, scored_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply dedup, diversity, tie-break, and optional priority boost."""
        deduped = self._deduplicate_by_offer_id(scored_rows)

        for row in deduped:
            priority_weight = float(row["offer"].get("priority_weight", 1.0))
            boost = (
                priority_weight * self._config.priority_boost_weight
                if self._config.priority_boost_enabled
                else 0.0
            )
            row["rerank_factors"]["priority_boost"] = boost
            row["boosted_score"] = row["normalized_score"] + boost

        by_score = sorted(
            deduped,
            key=lambda row: (
                -row["boosted_score"],
                -row["normalized_score"],
                row["offer"]["offer_id"],
            ),
        )

        primary: list[dict[str, Any]] = []
        overflow: list[dict[str, Any]] = []
        counts: defaultdict[str, int] = defaultdict(int)
        for row in by_score:
            offer_type = str(row["offer"]["offer_type"])
            if counts[offer_type] < self._config.max_per_offer_type:
                counts[offer_type] += 1
                primary.append(row)
            else:
                overflow.append(row)

        reranked = primary + overflow
        for index, row in enumerate(reranked, start=1):
            row["rerank_factors"]["raw_rank"] = row["raw_rank"]
            row["rerank_factors"]["reranked_rank"] = index
        return reranked

    def _deduplicate_by_offer_id(self, scored_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen_offer_ids: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for row in scored_rows:
            offer_id = str(row["offer"]["offer_id"])
            if offer_id in seen_offer_ids:
                continue
            seen_offer_ids.add(offer_id)
            deduped.append(row)
        return deduped

    def _load_config(self, config_path: Path) -> RerankConfig:
        if not config_path.exists():
            return RerankConfig()
        try:
            with config_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            return RerankConfig()

        if not isinstance(payload, dict):
            return RerankConfig()
        return RerankConfig(
            max_per_offer_type=int(payload.get("max_per_offer_type", 2)),
            priority_boost_enabled=bool(payload.get("priority_boost_enabled", True)),
            priority_boost_weight=float(payload.get("priority_boost_weight", 0.05)),
        )
