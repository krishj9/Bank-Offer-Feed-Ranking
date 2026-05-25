"""Tests for feedback endpoint."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_feedback_persists_jsonl_record(tmp_path: Path, monkeypatch) -> None:
    feedback_path = tmp_path / "feedback_events.jsonl"
    monkeypatch.setenv("FEEDBACK_STORE_PATH", str(feedback_path))

    client = TestClient(app)
    response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": "req_123",
            "user_id": "demo_user_001",
            "offer_id": "OFR-001",
            "action_type": "clicked",
            "model_version": "fallback-v1",
            "score": 0.77,
            "rank_position": 1,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"event_id", "status", "stored_at", "storage"}
    assert body["status"] == "stored"
    assert body["storage"] == "jsonl"
    assert body["event_id"]
    assert body["stored_at"]

    assert feedback_path.exists()
    lines = feedback_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["request_id"] == "req_123"
    assert record["offer_id"] == "OFR-001"
    assert record["action_type"] == "clicked"


def test_feedback_validation_rejects_unknown_action() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": "req_123",
            "user_id": "demo_user_001",
            "offer_id": "OFR-001",
            "action_type": "liked",
        },
    )
    assert response.status_code == 422


def test_feedback_metrics_report_from_stored_events(
    tmp_path: Path,
    monkeypatch,
) -> None:
    feedback_path = tmp_path / "feedback_events.jsonl"
    monkeypatch.setenv("FEEDBACK_STORE_PATH", str(feedback_path))
    client = TestClient(app)

    rank_response = client.post(
        "/api/v1/rank",
        json={
            "user_id": "demo_user_003",
            "top_k": 2,
        },
    )
    assert rank_response.status_code == 200

    feedback_response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": rank_response.json()["request_id"],
            "user_id": "demo_user_003",
            "offer_id": rank_response.json()["results"][0]["offer_id"],
            "action_type": "accepted",
            "model_version": rank_response.json()["model_version"],
            "feature_version": rank_response.json()["feature_version"],
            "rank_position": 1,
        },
    )
    assert feedback_response.status_code == 201

    metrics_response = client.get("/api/v1/feedback/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["summary"]["impressions"] == 2
    assert metrics["summary"]["feedback_events"] == 1
    assert metrics["summary"]["accept_proxy_events"] == 1
    assert metrics["summary"]["dismiss_proxy_events"] == 0
    assert metrics["summary"]["total_events"] == 3
    assert metrics["action_counts"]["viewed"] == 2
    assert metrics["action_counts"]["accepted"] == 1


def test_feedback_validation_rejects_invalid_rank_position() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": "req_123",
            "user_id": "demo_user_001",
            "offer_id": "OFR-001",
            "action_type": "clicked",
            "rank_position": 0,
        },
    )
    assert response.status_code == 422
