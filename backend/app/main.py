"""FastAPI application entrypoint."""

import logging
import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.rank import router as rank_router
from app.core.config import settings
from app.core.logging import (
    clear_request_context,
    configure_logging,
    log_event,
    set_request_context,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )
    app.include_router(health_router)
    app.include_router(rank_router)
    app.include_router(feedback_router)

    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", "").strip() or uuid4().hex
        correlation_id = request.headers.get("x-correlation-id", "").strip() or request_id
        set_request_context(request_id=request_id, correlation_id=correlation_id)
        try:
            response = await call_next(request)
        finally:
            clear_request_context()

        response.headers["x-request-id"] = request_id
        response.headers["x-correlation-id"] = correlation_id
        log_event(
            logging.getLogger(__name__),
            "request completed",
            event_type="http_request_completed",
            request_id=request_id,
            correlation_id=correlation_id,
            model_version="n/a",
            feature_version="n/a",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response

    return app


app = create_app()
