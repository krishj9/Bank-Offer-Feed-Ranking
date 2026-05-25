# Cursor Multitask Mode Rules

This repository is designed to be built in thin vertical slices by multiple Cursor agents working in parallel. 

## Ownership Boundaries
To minimize branch collision, the following role ownerships are defined:
- **Agent A (Product/Planner):** Specs refinement, ADRs, shared contracts (`shared/contracts/`), top-level documentation.
- **Agent B (Data Builder):** Data ingestion, preprocessing, synthetic data generation.
- **Agent C (ML Builder):** ML feature engineering, model training, offline evaluation, metrics.
- **Agent D (Backend Builder):** FastAPI ranking APIs, feedback APIs, API contracts (`backend/app/schemas/`).
- **Agent E (Frontend Builder):** React/Next.js UI, frontend API integration.
- **Agent F (Reviewer/QA):** Tests, linting, contract checks, integration review.
- **Agent G (Platform/CI):** Repo scaffold, dependency management, GitHub Actions, infrastructure.

## Coding Workflow
1. **Specification Adherence:** `specs/requirements.md` is the authoritative source. Agents must not edit the spec files (`specs/*.md`) unless explicitly requested.
2. **Task Isolation:** Each task prompt targets exact IDs from `specs/tasks.md`. Agents should focus only on their assigned scope.
3. **Shared Contracts Check:** Shared files (`shared/contracts/*`, `backend/app/schemas/*`, and global configs) require strict coordination and review before merging.
4. **Progress Tracking:** Update `agent/PROGRESS.md`, `agent/OPEN_QUESTIONS.md`, and `agent/DECISIONS.md` as task batches complete.
5. **Definition of Done:** 
   - Code is implemented.
   - Tests exist or are updated.
   - Documentation is aligned.
   - Lints and tests pass.
   - Artifacts (if any) are generated.
   - Progress notes are updated.
