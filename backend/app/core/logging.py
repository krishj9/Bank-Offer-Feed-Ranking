"""Structured logging setup and request logging context utilities."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")
_correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="unknown")
_BASE_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())


class StructuredJsonFormatter(logging.Formatter):
    """Format log records as JSON with standard ranking fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.app_env,
            "request_id": getattr(record, "request_id", _request_id_ctx.get()),
            "correlation_id": getattr(record, "correlation_id", _correlation_id_ctx.get()),
            "model_version": getattr(record, "model_version", "unknown"),
            "feature_version": getattr(record, "feature_version", "unknown"),
            "event_type": getattr(record, "event_type", "log"),
        }
        for key, value in record.__dict__.items():
            if key in _BASE_LOG_RECORD_FIELDS or key in payload:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def set_request_context(*, request_id: str, correlation_id: str) -> None:
    """Store request-scoped identifiers for downstream structured logs."""
    _request_id_ctx.set(request_id)
    _correlation_id_ctx.set(correlation_id)


def clear_request_context() -> None:
    """Reset request-scoped identifiers."""
    _request_id_ctx.set("unknown")
    _correlation_id_ctx.set("unknown")


def get_request_context() -> tuple[str, str]:
    """Return current request and correlation identifiers."""
    return _request_id_ctx.get(), _correlation_id_ctx.get()


def log_event(
    logger: logging.Logger,
    message: str,
    *,
    event_type: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
    model_version: str | None = None,
    feature_version: str | None = None,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Emit one structured event with required contextual fields."""
    logger.log(
        level,
        message,
        extra={
            "event_type": event_type,
            "request_id": request_id or _request_id_ctx.get(),
            "correlation_id": correlation_id or _correlation_id_ctx.get(),
            "model_version": model_version or "unknown",
            "feature_version": feature_version or "unknown",
            **fields,
        },
    )


def configure_logging() -> None:
    """Configure structured JSON logging for backend services."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    log_event(
        logging.getLogger(__name__),
        "logging configured",
        event_type="logging_configured",
    )
