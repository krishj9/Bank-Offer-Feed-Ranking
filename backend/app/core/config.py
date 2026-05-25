"""Application configuration."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Typed application settings loaded from environment variables."""

    app_name: str = os.getenv("APP_NAME", "Bank Offer Feed Ranking API")
    app_env: str = os.getenv("APP_ENV", "development")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    max_top_k: int = int(os.getenv("MAX_TOP_K", "20"))
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    sample_users_path: str = os.getenv(
        "SAMPLE_USERS_PATH",
        "data/processed/sample_users.json",
    )
    offers_path: str = os.getenv(
        "OFFERS_PATH",
        "data/synthetic/offers.csv",
    )
    feature_schema_path: str = os.getenv(
        "FEATURE_SCHEMA_PATH",
        "shared/contracts/feature_schema.json",
    )
    rerank_config_path: str = os.getenv(
        "RERANK_CONFIG_PATH",
        "backend/app/services/rerank_config.json",
    )
    feedback_store_path: str = os.getenv(
        "FEEDBACK_STORE_PATH",
        "data/processed/feedback_events.jsonl",
    )

    @property
    def repo_root(self) -> Path:
        """Resolve repository root from backend/app/core/config.py."""
        return Path(__file__).resolve().parents[3]

    def resolve_path(self, maybe_relative_path: str) -> Path:
        """Resolve absolute path for configured file path."""
        path = Path(maybe_relative_path).expanduser()
        if path.is_absolute():
            return path
        return (self.repo_root / path).resolve()


settings = Settings()
