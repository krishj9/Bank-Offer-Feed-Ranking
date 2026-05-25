#!/usr/bin/env python3
"""Validate committed ML artifact manifest structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "ml" / "artifacts" / "run_manifest.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "run_id",
    "model_type",
    "artifacts",
    "feature_names",
    "metrics",
}
REQUIRED_ARTIFACT_KEYS = {"model", "preprocessor"}


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []

    missing_keys = REQUIRED_TOP_LEVEL_KEYS - manifest.keys()
    if missing_keys:
        errors.append(f"run_manifest missing keys: {sorted(missing_keys)}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("artifacts section must be an object")
        return errors

    missing_artifact_keys = REQUIRED_ARTIFACT_KEYS - artifacts.keys()
    if missing_artifact_keys:
        errors.append(
            f"artifacts section missing keys: {sorted(missing_artifact_keys)}"
        )

    preprocessor_rel = artifacts.get("preprocessor")
    if isinstance(preprocessor_rel, str):
        preprocessor_path = REPO_ROOT / preprocessor_rel
        if preprocessor_path.exists():
            try:
                with preprocessor_path.open(encoding="utf-8") as file:
                    json.load(file)
            except json.JSONDecodeError as exc:
                errors.append(f"preprocessor artifact is invalid JSON: {exc}")

    model_rel = artifacts.get("model")
    if isinstance(model_rel, str):
        model_path = REPO_ROOT / model_rel
        if not model_path.exists():
            print(
                f"NOTE: model artifact not present at {model_rel} "
                "(expected when large binaries are gitignored)"
            )

    return errors


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"WARNING: {MANIFEST_PATH} not found; skipping artifact check")
        return 0

    with MANIFEST_PATH.open(encoding="utf-8") as file:
        manifest = json.load(file)

    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("ML artifact manifest validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
