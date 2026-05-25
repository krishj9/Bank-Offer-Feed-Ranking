#!/usr/bin/env bash
# Local quality gate: one command for core lint, type-check, and test checks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

run_python() {
  if command -v uv >/dev/null 2>&1; then
    uv sync --extra dev >/dev/null
    uv run "$@"
  elif [[ -f ".venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
    "$@"
  else
    echo "ERROR: install dependencies with 'uv sync --dev' or create .venv first."
    exit 1
  fi
}

echo "== Backend lint =="
run_python ruff check backend shared/tests

echo "== Backend type-check =="
run_python mypy

echo "== Backend tests =="
run_python pytest backend/tests shared/tests -q

echo "== ML lint =="
run_python ruff check ml shared

echo "== ML smoke tests =="
run_python pytest ml/tests -q

echo "== ML artifact check =="
run_python python scripts/check_ml_artifacts.py

if [[ ! -d "frontend/node_modules" ]]; then
  echo "== Frontend bootstrap =="
  npm run bootstrap
fi

echo "== Frontend lint =="
npm run lint --prefix frontend

echo "== Frontend tests =="
npm run test --prefix frontend

echo
echo "All quality checks passed."
