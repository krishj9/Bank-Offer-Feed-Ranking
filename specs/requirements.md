Document ID: REQ-BOFR-001
Version: 1.0
Status: Draft
Project: Bank Offer Feed Ranking
Last Updated: 2026-05-24
Owner: Product / Engineering

# 1. Purpose

Build a production-aligned machine learning application that ranks bank offers for a customer in a feed-style interface using public and synthetic data.

The system shall simulate a banking app experience where a user sees a ranked list of offers such as term deposit, savings boost, credit card, financial wellness session, refinance prompt, or advisor callback. The ranking shall be personalized using customer attributes, historical interaction patterns, contextual signals, and business rules.

The project shall demonstrate:
- Ranking-system design rather than only binary classification.
- Conversion of public tabular campaign data into a recommendation-style problem.
- Production-aligned engineering practices using spec-driven development.
- Modular development that works well with Cursor Multitask mode.
- Explainability, observability, and feedback-aware iteration.

This project shall use the UCI / Kaggle Bank Marketing dataset as the primary real dataset. The original dataset predicts whether a customer subscribes to a term deposit after direct marketing contact, and the duration field is known to be highly target-leaking; therefore, the system shall exclude `duration` from default training and serving features unless explicitly enabled for offline experimentation only. [web:33][web:94]

# 2. Goals

The system shall:
- Rank candidate offers for a given user rather than return only a single yes/no prediction.
- Support synthetic offer generation and synthetic interaction generation on top of the public customer dataset.
- Provide a working end-to-end application with training, inference, UI display, and feedback capture.
- Be implementable in phased slices by multiple Cursor agents working in parallel on well-bounded tasks. [cite:90]

The project should demonstrate the following engineering qualities:
- Clear contracts between data, model, API, and UI layers.
- Reproducible training and evaluation.
- Traceable predictions with model version and feature provenance.
- Basic explainability for why an offer was ranked highly.
- Monitoring hooks for product, system, and model metrics.

# 3. Non-Goals

The system shall not:
- Perform real banking transactions.
- Use real customer PII or private financial records.
- Attempt production-grade regulatory decisioning.
- Depend on a vector database in version 1 unless retrieval-based explanation augmentation is explicitly added later.
- Build a full reinforcement learning system in version 1.
- Optimize for true production scale, high availability, or complex multi-region deployment in version 1.

# 4. Users and Roles

## 4.1 Primary user

The primary end user shall be a simulated banking customer profile viewer inside the demo application. This user interacts with a ranked feed of offers.

## 4.2 Secondary user

The secondary user shall be the developer, reviewer, or product operator who:
- triggers model training,
- inspects rankings,
- reviews explanations,
- validates metrics,
- tests feedback loops,
- reviews experiment outputs.

## 4.3 Build-time agent roles

The project shall support a multi-agent implementation workflow in Cursor Multitask mode with role-aligned responsibilities such as:
- Product/Planner agent,
- Builder/Developer agent,
- Reviewer/QA agent,
- Optional Platform/Infra agent. [cite:90]

These agent roles are implementation workflow roles only and shall not be exposed as runtime product personas.

# 5. Functional Requirements

## 5.1 Data ingestion

FR-001  
The system shall ingest the Bank Marketing dataset from a local project data directory in CSV form.

FR-002  
The system shall validate incoming dataset schema, required columns, data types, null handling expectations, and allowed categorical values where applicable.

FR-003  
The system shall produce a cleaned and standardized dataset artifact for downstream feature engineering and training.

FR-004  
The system shall exclude `duration` from default model training and inference because it is not a realistic decision-time feature and is documented as highly predictive due to target leakage. [web:94][web:33]

FR-005  
The system shall log dataset version, row count, schema summary, and preprocessing summary for reproducibility.

## 5.2 Synthetic offer catalog

FR-006  
The system shall generate or load a synthetic offer catalog that contains multiple offer types suitable for a retail banking feed.

FR-007  
Each offer shall have structured metadata including:
- offer_id,
- offer_type,
- title,
- short_description,
- product_category,
- eligibility_rules,
- priority_weight,
- active_status,
- created_at or version tag.

FR-008  
The system shall support at least five distinct offer types in version 1.

## 5.3 Candidate generation

FR-009  
The system shall generate a candidate offer set for a user before ranking.

FR-010  
Candidate generation shall support rule-based eligibility filtering such as age band, job category proxy, contact preference, prior campaign count, and selected business constraints.

FR-011  
The system shall allow both:
- a simple “all eligible offers” candidate strategy, and
- an extensible candidate generator abstraction for later experimentation.

## 5.4 Feature engineering

FR-012  
The system shall create user-level, offer-level, and user-offer interaction features.

FR-013  
User-level features shall include customer profile and campaign history features derived from the dataset.

FR-014  
Offer-level features shall include offer metadata, offer type, offer priority, and optional business tags.

FR-015  
User-offer features shall include eligibility match signals, affinity heuristics, contextual compatibility, and synthetic historical interaction aggregates.

FR-016  
The same feature definitions used in training shall be reusable during inference to reduce training-serving skew, which is a core MLOps concern. [web:59][web:65]

## 5.5 Label generation

FR-017  
The system shall support supervised training labels for ranking derived from a mix of:
- original dataset target,
- synthetic click labels,
- synthetic accept labels,
- synthetic ignore or negative labels.

FR-018  
The system shall support at least one baseline label-generation strategy that is deterministic and documented.

FR-019  
The system should support future extension to multiple task labels such as click, accept, hide, and dwell proxy for multi-objective ranking.

## 5.6 Model training

FR-020  
The system shall support a baseline training pipeline.

FR-021  
The baseline model may be a pointwise ranker implemented using a classification model over user-offer pairs.

FR-022  
The training pipeline shall save:
- model artifact,
- preprocessing artifact,
- feature metadata,
- evaluation report,
- run metadata.

FR-023  
The training pipeline shall be executable from command line or task runner without requiring notebook execution.

FR-024  
The system shall support retraining on refreshed synthetic interaction data.

FR-025  
The project should start with a simple baseline such as logistic regression, random forest, gradient boosting, XGBoost, or LightGBM, then leave room for later reranking improvements. Public examples on this dataset commonly compare multiple classifiers and emphasize class imbalance handling and careful evaluation. [web:100]

## 5.7 Ranking service

FR-026  
The system shall expose an API that accepts a customer profile or customer identifier and returns a ranked list of offers.

FR-027  
Each ranked result shall include:
- rank position,
- offer_id,
- offer title,
- model score,
- confidence or normalized relevance score,
- explanation summary,
- model version,
- request identifier.

FR-028  
The ranking service shall support top-K retrieval for a caller-specified K within configured limits.

FR-029  
The ranking service shall support deterministic sorting rules when model scores tie.

FR-030  
The ranking service shall support post-processing rules for diversity, freshness, or business priority, because modern recommendation systems commonly rerank for criteria beyond raw relevance. [web:98][web:107]

## 5.8 Reranking and business rules

FR-031  
The system shall support a reranking layer after model scoring.

FR-032  
The reranking layer shall support:
- diversity by offer type,
- optional freshness boost,
- optional priority boost,
- suppression of duplicate or near-duplicate offers.

FR-033  
The reranking configuration shall be externalized so business rules can change without retraining the model.

FR-034  
The system should support experimentation with multiple ranking objectives such as conversion likelihood, diversity, and negative-feedback avoidance. Recommendation-system guidance highlights diversity, fairness, and freshness as important reranking criteria. [web:98][web:107]

## 5.9 Explanations

FR-035  
The system shall provide a short human-readable explanation for each ranked offer.

FR-036  
Version 1 explanations may be deterministic and template-based using top contributing features or business rules.

FR-037  
The system should support a future optional LLM-based explanation layer, but ranking shall not depend on LLM availability in version 1.

FR-038  
The explanation layer shall avoid claiming causal certainty and shall present signals as likely contributing factors.

## 5.10 Feedback capture

FR-039  
The system shall capture user feedback events such as:
- viewed,
- clicked,
- accepted,
- dismissed,
- not interested.

FR-040  
Feedback events shall be stored in a structured format suitable for later analysis and retraining.

FR-041  
The system shall associate feedback events with request ID, offer ID, user ID or synthetic user key, timestamp, and model version.

## 5.11 UI requirements

FR-042  
The system shall provide a simple web UI that displays:
- a selected customer profile,
- ranked offers,
- score or confidence indication,
- explanation summary,
- feedback actions.

FR-043  
The UI shall allow switching among sample customer profiles.

FR-044  
The UI shall allow the operator to trigger a rerank after recording feedback in demo mode.

FR-045  
The UI shall surface enough metadata to make the ranking logic inspectable for portfolio and interview demonstration purposes.

## 5.12 Observability

FR-046  
The system shall emit structured logs for:
- training runs,
- inference requests,
- ranking outputs,
- feedback events,
- errors.

FR-047  
The system shall track core product and model metrics such as:
- impressions,
- clicks,
- accepts,
- dismiss rate,
- CTR,
- top-K conversion proxy,
- latency,
- error rate.

FR-048  
The system shall make model version, dataset version, and feature version visible in training and inference records.

FR-049  
The system should support tracing or experiment metadata capture for later integration with LangSmith or a similar observability tool, consistent with the user’s preferred stack. [cite:2]

## 5.13 Evaluation

FR-050  
The system shall provide offline evaluation for the baseline model.

FR-051  
Offline evaluation shall include classification metrics and ranking metrics appropriate to the selected modeling formulation.

FR-052  
The system shall include at least one top-K oriented evaluation view such as Precision@K, Recall@K, MAP, or NDCG.

FR-053  
The system shall support slice-based evaluation across selected subgroups or feature ranges to inspect uneven performance. Recommendation-system best practices advise tracking bias and performance across groups, not only global metrics. [web:98]

FR-054  
The system shall document known limitations of synthetic labels and synthetic interactions.

# 6. Non-Functional Requirements

## 6.1 Architecture

NFR-001  
The system shall use a modular architecture separating:
- data ingestion,
- feature engineering,
- training,
- inference,
- reranking,
- explanation,
- feedback capture,
- UI.

NFR-002  
The architecture shall be suitable for phased parallel implementation using Cursor Multitask mode by assigning bounded modules to different agents. [cite:90]

NFR-003  
The system shall expose clear interfaces between modules to reduce agent collision and integration ambiguity.

## 6.2 Reproducibility

NFR-004  
The system shall make training runs reproducible through configuration, fixed seeds where appropriate, saved artifacts, and logged metadata.

NFR-005  
The project shall store enough metadata to reproduce a ranking result from the same model version and feature inputs.

## 6.3 Performance

NFR-006  
The local demo inference path should return a top-K ranking response within a reasonable interactive latency target for a single user request under development conditions.

NFR-007  
The system should support ranking at least dozens to hundreds of candidates per request in version 1.

## 6.4 Reliability

NFR-008  
The system shall fail gracefully when:
- model artifacts are missing,
- input schema is invalid,
- no eligible offers exist,
- explanation generation fails.

NFR-009  
If explanation generation fails, the ranking service shall still return ranked offers with a fallback explanation state.

## 6.5 Security and privacy

NFR-010  
The system shall use only public and synthetic data in version 1.

NFR-011  
The system shall avoid storing secrets in source control and shall use environment-based configuration for sensitive values.

NFR-012  
The project should follow secure-by-design principles and CI-integrated checks, consistent with modern secure software practices. [web:53][web:58]

## 6.6 Responsible AI

NFR-013  
The system shall document the intended use, limitations, and known risks of the ranking model.

NFR-014  
The system shall support human inspection of ranked outputs and explanations.

NFR-015  
The system shall include documented monitoring and review hooks for bias, drift, and performance degradation, which align with AI risk-management guidance emphasizing governance, transparency, monitoring, and human oversight. [web:99][web:102][web:105]

# 7. Data Assumptions

DA-001  
The primary real dataset shall be the UCI Bank Marketing dataset or a Kaggle-hosted equivalent derived from it. The dataset concerns direct marketing campaigns of a Portuguese banking institution. [web:33]

DA-002  
Synthetic offer records and synthetic interaction records shall be generated locally by project code and stored as versioned artifacts.

DA-003  
No external live banking APIs shall be required for version 1.

DA-004  
Synthetic labels shall be clearly marked as synthetic in all documentation and evaluation outputs.

# 8. Acceptance Criteria

AC-001  
A developer can load the Bank Marketing dataset, run preprocessing, and produce a cleaned training-ready dataset artifact.

AC-002  
A developer can generate a synthetic offer catalog and user-offer candidate pairs.

AC-003  
A developer can train a baseline ranking model and save model artifacts plus an evaluation report.

AC-004  
A caller can invoke an API with a user or profile payload and receive a ranked top-K offer list.

AC-005  
The returned list includes scores, rank order, model version, and explanation summary for each offer.

AC-006  
The web UI displays a ranked feed for a selected sample user and allows at least one feedback action.

AC-007  
Feedback events are persisted and can be replayed or inspected.

AC-008  
The reranking layer can be configured to change feed composition without retraining the base model.

AC-009  
The project contains sufficient modular boundaries for multiple Cursor agents to work in parallel on at least:
- data layer,
- model layer,
- API layer,
- UI layer,
- review or test layer. [cite:90]

AC-010  
The documentation clearly states that `duration` is excluded by default from modeling because it creates unrealistic leakage for decision-time prediction. [web:94][web:33]

# 9. Suggested Implementation Boundaries for Cursor Multitask Mode

The project should be decomposed so parallel Cursor agents can work with minimal overlap.

Recommended boundaries:
- Agent A: requirements and design refinement, schema contracts, ADRs.
- Agent B: data ingestion, preprocessing, synthetic offer generation.
- Agent C: model training, evaluation, artifact packaging.
- Agent D: FastAPI ranking service, request and response contracts.
- Agent E: React UI for ranked feed and feedback capture.
- Agent F: reviewer or QA agent for tests, linting, contract validation, and integration review. [cite:90]

All agents shall treat this requirements document as the authoritative source of scope until superseded by an approved design document.

# 10. Out of Scope for Version 1

- Online learning.
- Reinforcement learning.
- Real-time event streaming infrastructure.
- Production IAM hardening beyond reasonable demo scaffolding.
- Feature store infrastructure.
- Full model registry platform.
- Real customer identity integration.
- Live A/B experimentation platform.
- LLM-generated financial advice.