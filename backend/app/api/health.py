"""Health check endpoints."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.model_loader import ModelArtifactLoader

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> JSONResponse:
    """Return service health status."""
    loaded = ModelArtifactLoader().load()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ok",
            "model_ready": loaded.ready,
            "artifacts_dir": str(loaded.artifacts_dir),
            "artifact_status": {
                "model": loaded.model_status.available,
                "preprocessor": loaded.preprocessor_status.available,
                "manifest": loaded.manifest_status.available,
            },
        },
    )
