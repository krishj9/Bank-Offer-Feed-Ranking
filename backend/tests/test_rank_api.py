"""Tests for rank and sample-user APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.model_loader import ArtifactStatus, LoadedArtifacts
from app.main import app


def test_rank_returns_top_k_ranked_results() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/rank",
        json={
            "user_id": "demo_user_003",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "request_id",
        "model_version",
        "feature_version",
        "generated_at",
        "results",
        "warnings",
    }
    assert len(body["results"]) == 3
    assert [item["rank"] for item in body["results"]] == [1, 2, 3]
    assert all(item["request_id"] == body["request_id"] for item in body["results"])
    assert body["results"][0]["request_id"] == body["request_id"]
    assert body["results"][0]["offer_id"]


def test_rank_handles_no_eligible_offers_gracefully() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/rank",
        json={
            "user_profile": {
                "user_id": "no_eligible_user",
                "age": 18,
                "job": "student",
                "marital": "married",
                "education": "basic.9y",
                "default": "no",
                "housing": "no",
                "loan": "yes",
                "contact": "cellular",
                "month": "apr",
                "day_of_week": "mon",
                "campaign": 1,
                "pdays": 999,
                "previous": 0,
                "poutcome": "nonexistent",
                "emp_var_rate": -1.8,
                "cons_price_idx": 93.075,
                "cons_conf_idx": -47.1,
                "euribor3m": 1.405,
                "nr_employed": 5099.1,
            },
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert "No eligible offers" in body["warnings"][0]


def test_rank_falls_back_when_artifacts_are_missing(monkeypatch) -> None:
    client = TestClient(app)
    missing = ArtifactStatus(available=False, path=Path("/tmp/missing"), error="missing")
    monkeypatch.setattr(
        "app.api.rank._ranking_service._artifact_loader.load",
        lambda: LoadedArtifacts(
            artifacts_dir=Path("/tmp"),
            model=None,
            preprocessor=None,
            manifest=None,
            model_status=missing,
            preprocessor_status=missing,
            manifest_status=missing,
        ),
    )

    response = client.post(
        "/api/v1/rank",
        json={
            "user_id": "demo_user_003",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "fallback-v1"
    assert body["feature_version"] == "feature-default-v1"
    assert len(body["results"]) == 3
    assert "Model artifacts unavailable" in body["warnings"][0]


def test_rank_validation_requires_user_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/rank",
        json={"top_k": 5},
    )
    assert response.status_code == 422


def test_rank_validation_rejects_out_of_range_top_k() -> None:
    client = TestClient(app)
    too_low = client.post(
        "/api/v1/rank",
        json={"user_id": "demo_user_003", "top_k": 0},
    )
    too_high = client.post(
        "/api/v1/rank",
        json={"user_id": "demo_user_003", "top_k": 21},
    )
    assert too_low.status_code == 422
    assert too_high.status_code == 422


def test_sample_users_returns_profiles() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/sample-users")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 10
    assert body["count"] == len(body["users"])
    assert set(body["users"][0]) == {
        "user_id",
        "age",
        "job",
        "marital",
        "education",
        "default",
        "housing",
        "loan",
        "contact",
        "month",
        "day_of_week",
        "campaign",
        "pdays",
        "previous",
        "poutcome",
        "emp_var_rate",
        "cons_price_idx",
        "cons_conf_idx",
        "euribor3m",
        "nr_employed",
    }
    assert body["users"][0]["user_id"].startswith("demo_user_")
