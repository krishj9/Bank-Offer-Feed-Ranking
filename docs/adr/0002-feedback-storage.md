# ADR 0002: Feedback Storage Mechanism

## Status
Accepted

## Context
The system needs to capture and persist user interactions (viewed, clicked, accepted, dismissed) from the React UI to measure performance and enable future offline retraining.

## Decision
We chose a local **JSONL (JSON Lines)** file (`data/processed/feedback_events.jsonl`) for feedback and impression persistence in Version 1.

## Rationale
- **Simplicity:** JSONL is an append-only format that requires no external database infrastructure (like PostgreSQL or DynamoDB) to run locally.
- **Schema Evolution:** Easy to append varied metadata without strict migration scripts.
- **Integration:** Perfect format for Pandas/Polars to consume directly during offline data preparation for V2 retraining.

## Consequences
- Single-node concurrency limitations exist, but are perfectly acceptable for a local demo application.
- Product metrics reporting requires scanning the file sequentially rather than executing SQL aggregations.