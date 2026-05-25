# ADR 0004: LLM Explanation Deferral

## Status
Accepted

## Context
The requirements requested short, human-readable explanations for why an offer was ranked highly. Modern systems often use Large Language Models (LLMs) to synthesize these features into natural language.

## Decision
We explicitly **deferred** LLM integration for Version 1. Instead, we use a deterministic, template-based explanation service (`backend/app/services/explanation_service.py`).

## Rationale
- **Reliability:** Template-based explanations guarantee a sub-millisecond response and cannot hallucinate.
- **Simplicity:** Avoids complex external dependencies, API keys (e.g., AWS Bedrock, OpenAI), and rate-limiting during local development.
- **Scope Alignment:** Keeps the V1 focus purely on the ML ranking architecture and the deterministic MLOps pipeline.

## Consequences
- Explanations are robotic and rigidly structured.
- Paves the way for an easy V2 upgrade where the template text can be passed to an LLM for stylistic rewriting.