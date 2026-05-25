# Bank Offer Feed Ranking

## Overview
A production-aligned machine learning application that ranks synthetic bank offers for customers in a feed-style interface using public tabular data (UCI Bank Marketing dataset). The system simulates a banking app experience by personalizing ranked offers (e.g., term deposit, savings boost, credit card) based on customer attributes, interaction patterns, and business rules.

## Architecture
The system is built as a modular monorepo separated into seven logical layers:
1. **Data Layer:** Loads and cleans the UCI Bank Marketing CSV dataset.
2. **Synthetic Scenario Layer:** Generates synthetic offers and user-offer candidates/labels.
3. **Feature Layer:** Produces offline and online features for users and offers, sharing logic to prevent training-serving skew.
4. **Model Layer:** Trains a baseline ranking model (Point-wise HistGradientBoostingClassifier).
5. **Ranking Application Layer:** Orchestrates candidate selection, scoring, reranking, and explainability.
6. **Experience Layer:** Exposes the API (FastAPI) and a UI feed (React SPA).
7. **Observability & Delivery Layer:** Handles logging, metrics, artifacts, and CI/CD.

## Setup Instructions
Please refer to the following guides for detailed setup, training, inference, and UI startup instructions:
- [Local Installation Guide](docs/install-local.md) - Run the full app locally.
- [AWS Deployment Guide](docs/install-aws.md) - EC2 (stop when idle) or serverless (S3 + CloudFront + Lambda) deployment.
- [Developer Runbook](docs/runbook.md) - Deep dive into developer commands and workflows.

## Dataset Attribution
This project uses the `bank-additional-full.csv` from the **UCI Bank Marketing dataset** (licensed under CC BY 4.0).
*Source: Moro, S., Rita, P., and Cortez, P. (2014). Bank Marketing.*

## Demo Flow
1. **Select User:** The operator selects a sample user from the UI.
2. **Candidate Generation & Scoring:** The backend dynamically loads user features, generates eligible candidate offers, scores them via the trained ML model, and normalizes scores.
3. **Reranking:** Business rules (diversity, priority) rerank the results.
4. **Feed Display:** UI displays the ranked offers with explanations.
5. **Feedback Loop:** User feedback (viewed, clicked, accepted) is captured in a JSONL event store to inform metrics and future model iteration.

## Known Limitations
- **Synthetic Bias:** Offer attributes and labels are generated synthetically based on heuristics.
- **Cold Start:** New users without demographic history receive baseline default rankings.
- **Static Model:** Version 1 relies on a static pre-trained `joblib` artifact without real-time online learning.
- **Data Leakage Mitigation:** The highly predictive `duration` feature from the UCI dataset is completely excluded by design as it represents post-decision information (duration of a call).