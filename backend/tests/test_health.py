"""Health endpoint tests."""

from app.main import app
from fastapi.testclient import TestClient


def test_health_returns_200() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["model_ready"], bool)
    assert isinstance(body["artifacts_dir"], str)
    assert set(body["artifact_status"]) == {"model", "preprocessor", "manifest"}
