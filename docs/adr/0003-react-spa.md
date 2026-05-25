# ADR 0003: Frontend Architecture (React SPA)

## Status
Accepted

## Context
We require a demo UI to showcase the ranked bank offers, capture user feedback, and provide developer diagnostics.

## Decision
We chose a **React Single Page Application (SPA)** built with Vite (and Tailwind CSS) rather than a full-stack Next.js SSR application.

## Rationale
- **Clear Boundaries:** Enforces strict separation between the Experience Layer (UI) and the Ranking Application Layer (FastAPI). The frontend acts as a pure API consumer.
- **Simplicity:** Simplifies local setup for Cursor Multitask mode. The backend handles all data-fetching and logic; the UI strictly handles presentation and state tracking.
- **Speed:** Fast compilation and hot-reloading for the UI developer agent.

## Consequences
- No Server-Side Rendering (SSR) benefits (SEO, initial paint), which are irrelevant for a local enterprise demo application.
- Relies entirely on CORS and API availability from the FastAPI server.