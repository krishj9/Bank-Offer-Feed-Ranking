"""Tests for backend-safe model artifact loader."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

from app.core.model_loader import ModelArtifactLoader


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file)


def _write_pickled_model(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        pickle.dump({"model_name": "baseline"}, file)


def test_artifact_loader_loads_all_available_artifacts(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "ml" / "artifacts"
    model_path = artifacts_dir / "baseline_model.joblib"
    preprocessor_path = artifacts_dir / "preprocessor.json"
    manifest_path = artifacts_dir / "run_manifest.json"

    _write_pickled_model(model_path)
    _write_json(preprocessor_path, {"feature_version": "v1"})
    _write_json(
        manifest_path,
        {
            "run_id": "run_1",
            "artifacts": {
                "model": str(model_path),
                "preprocessor": str(preprocessor_path),
            },
        },
    )

    loader = ModelArtifactLoader(artifacts_dir=artifacts_dir)
    loaded = loader.load()

    assert loaded.ready is True
    assert loaded.model == {"model_name": "baseline"}
    assert loaded.preprocessor == {"feature_version": "v1"}
    assert loaded.manifest is not None
    assert loaded.model_status.available is True
    assert loaded.preprocessor_status.available is True
    assert loaded.manifest_status.available is True


def test_artifact_loader_handles_missing_model_gracefully(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    preprocessor_path = artifacts_dir / "preprocessor.json"
    manifest_path = artifacts_dir / "run_manifest.json"

    _write_json(preprocessor_path, {"feature_version": "v1"})
    _write_json(
        manifest_path,
        {
            "run_id": "run_2",
            "artifacts": {
                "model": str(artifacts_dir / "baseline_model.joblib"),
                "preprocessor": str(preprocessor_path),
            },
        },
    )

    loader = ModelArtifactLoader(artifacts_dir=artifacts_dir)
    loaded = loader.load()

    assert loaded.ready is False
    assert loaded.model is None
    assert loaded.preprocessor == {"feature_version": "v1"}
    assert loaded.model_status.available is False
    assert loaded.model_status.error is not None
    assert "Missing artifact file" in loaded.model_status.error


def test_artifact_loader_falls_back_without_manifest(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    model_path = artifacts_dir / "baseline_model.joblib"
    preprocessor_path = artifacts_dir / "preprocessor.json"

    _write_pickled_model(model_path)
    _write_json(preprocessor_path, {"feature_version": "fallback"})

    loader = ModelArtifactLoader(artifacts_dir=artifacts_dir)
    loaded = loader.load()

    assert loaded.ready is False
    assert loaded.model == {"model_name": "baseline"}
    assert loaded.preprocessor == {"feature_version": "fallback"}
    assert loaded.model_status.available is True
    assert loaded.preprocessor_status.available is True
    assert loaded.manifest_status.available is False
    assert loaded.manifest is None
