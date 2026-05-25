Document ID: DES-BOFR-001
Version: 1.0
Status: Draft
Project: Bank Offer Feed Ranking
Last Updated: 2026-05-24
Owner: Engineering

# 1. Purpose

This document defines the solution design for Bank Offer Feed Ranking, a production-aligned ML application that ranks synthetic bank offers for users using the UCI Bank Marketing dataset as the core customer-history dataset.

The design supports:
- spec-driven development,
- parallel implementation in Cursor Multitask mode,
- clear module boundaries,
- reproducible ML training and inference,
- explainability and observability,
- future extensibility for richer ranking and LLM-assisted explanation.

This design uses `bank-additional-full.csv` from the UCI Bank Marketing dataset as the primary real dataset. UCI describes this file as the full version with 41,188 rows and 20 inputs plus the target, and the dataset is licensed under CC BY 4.0. [web:33][web:111]

# 2. Design Principles

The architecture shall follow these principles:
- Keep version 1 simple and end-to-end.
- Separate training, inference, reranking, explanation, and UI concerns.
- Avoid training-serving skew by reusing the same feature logic across offline and online paths, which is a recognized MLOps best practice. [web:119][web:122]
- Prefer deterministic explanations in version 1 so the ranking path is not dependent on an LLM.
- Make modules independently buildable by different Cursor agents.
- Use interfaces and contracts early to reduce branch collision in parallel development. [cite:90]

# 3. High-Level Architecture

The system consists of seven logical layers:

1. Data layer  
   Loads `bank-additional-full.csv`, validates schema, standardizes fields, and creates cleaned artifacts. [web:33]

2. Synthetic scenario layer  
   Generates synthetic offers, synthetic user-offer candidates, and synthetic interaction labels.

3. Feature layer  
   Produces reusable offline and online features for user, offer, and user-offer pairs.

4. Model layer  
   Trains a baseline ranker and generates ranked scores for candidate offers.

5. Ranking application layer  
   Applies candidate selection, scoring, reranking, explanation, and response formatting.

6. Experience layer  
   Exposes APIs through FastAPI and a feed-style UI through React.

7. Observability and delivery layer  
   Captures logs, metrics, artifacts, CI/CD, and infrastructure definitions.

# 4. Runtime Flow

## 4.1 Training flow

The offline training flow shall be:

1. Load raw CSV from `data/raw/bank-additional-full.csv`.
2. Validate schema and required columns.
3. Clean and normalize dataset values.
4. Exclude `duration` from default feature set because it creates unrealistic leakage for decision-time prediction, which is explicitly noted in material based on the UCI dataset. [web:33][web:95]
5. Generate synthetic offer catalog.
6. Generate user-offer training pairs.
7. Generate supervised training labels.
8. Build training features using shared feature code.
9. Train baseline ranking model.
10. Evaluate model using both classification and ranking metrics.
11. Save artifacts, metadata, and evaluation outputs.

## 4.2 Inference flow

The online inference flow shall be:

1. Receive ranking request for a selected user or payload.
2. Load or construct user profile.
3. Generate eligible offer candidates.
4. Build online features using the same reusable feature logic used in training to reduce training-serving skew. [web:119][web:122]
5. Score candidates with the deployed model.
6. Apply reranking 