"""Backend-safe model artifact loader.

This module intentionally avoids importing any ML training package/module from
the repository so API routes can load inference artifacts without coupling to
training code.
"""

from __future__ import annotations

import json
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ARTIFACTS_DIR_ENV = "MODEL_ARTIFACTS_DIR"


def _repo_root() -> Path:
    """Return repository root based on this file location."""
    return Path(__file__).resolve().parents[3]


def _default_artifacts_dir() -> Path:
    """Resolve artifact directory from env or default location."""
    env_value = os.getenv(ARTIFACTS_DIR_ENV)
    if env_value:
        return Path(env_value).expanduser().resolve()
    return _repo_root() / "ml" / "artifacts"


@dataclass(frozen=True)
class ArtifactStatus:
    """Status for a single artifact load operation."""

    available: bool
    path: Path
    error: str | None = None


@dataclass(frozen=True)
class LoadedArtifacts:
    """Loaded artifact payload with per-file status details."""

    artifacts_dir: Path
    model: Any | None
    preprocessor: dict[str, Any] | None
    manifest: dict[str, Any] | None
    model_status: ArtifactStatus
    preprocessor_status: ArtifactStatus
    manifest_status: ArtifactStatus

    @property
    def ready(self) -> bool:
        """True when model + feature artifacts are fully loaded."""
        return (
            self.model_status.available
            and self.preprocessor_status.available
            and self.manifest_status.available
        )


class ModelArtifactLoader:
    """Load model/preprocessor/manifest artifacts for inference."""

    def __init__(self, artifacts_dir: Path | None = None) -> None:
        self._artifacts_dir = artifacts_dir or _default_artifacts_dir()

    @property
    def artifacts_dir(self) -> Path:
        """Directory where artifacts are expected."""
        return self._artifacts_dir

    def load(self) -> LoadedArtifacts:
        """Load known model artifacts, returning graceful status on failures."""
        manifest_path = self._artifacts_dir / "run_manifest.json"
        manifest, manifest_status = self._load_json(manifest_path)

        model_path = self._resolve_artifact_path(
            manifest=manifest,
            key="model",
            default_filename="baseline_model.joblib",
        )
        preprocessor_path = self._resolve_artifact_path(
            manifest=manifest,
            key="preprocessor",
            default_filename="preprocessor.json",
        )

        model, model_status = self._load_model(model_path)
        preprocessor, preprocessor_status = self._load_json(preprocessor_path)

        return LoadedArtifacts(
            artifacts_dir=self._artifacts_dir,
            model=model,
            preprocessor=preprocessor,
            manifest=manifest,
            model_status=model_status,
            preprocessor_status=preprocessor_status,
            manifest_status=manifest_status,
        )

    def _resolve_artifact_path(
        self,
        *,
        manifest: dict[str, Any] | None,
        key: str,
        default_filename: str,
    ) -> Path:
        """Resolve artifact path from manifest, then fall back to artifacts dir."""
        if not manifest:
            return self._artifacts_dir / default_filename

        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            return self._artifacts_dir / default_filename

        candidate = artifacts.get(key)
        if not isinstance(candidate, str) or not candidate.strip():
            return self._artifacts_dir / default_filename

        candidate_path = Path(candidate)
        if candidate_path.is_absolute():
            return candidate_path
        return (_repo_root() / candidate_path).resolve()

    def _load_json(self, path: Path) -> tuple[dict[str, Any] | None, ArtifactStatus]:
        """Load JSON artifact at path."""
        if not path.exists():
            return None, ArtifactStatus(
                available=False,
                path=path,
                error=f"Missing artifact file: {path}",
            )

        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            return None, ArtifactStatus(
                available=False,
                path=path,
                error=f"Failed to load JSON artifact: {exc}",
            )

        if not isinstance(payload, dict):
            return None, ArtifactStatus(
                available=False,
                path=path,
                error="JSON artifact must contain an object.",
            )

        return payload, ArtifactStatus(available=True, path=path, error=None)

    def _load_model(self, path: Path) -> tuple[Any | None, ArtifactStatus]:
        """Load serialized model artifact."""
        if not path.exists():
            return None, ArtifactStatus(
                available=False,
                path=path,
                error=f"Missing artifact file: {path}",
            )

        try:
            model = self._deserialize_model(path)
        except Exception as exc:  # noqa: BLE001 - surface all model load failures
            return None, ArtifactStatus(
                available=False,
                path=path,
                error=f"Failed to load model artifact: {exc}",
            )

        return model, ArtifactStatus(available=True, path=path, error=None)

    def _deserialize_model(self, path: Path) -> Any:
        """Deserialize model using joblib if available, else pickle."""
        try:
            import joblib
        except ImportError:
            with path.open("rb") as file:
                return pickle.load(file)
        return joblib.load(path)

