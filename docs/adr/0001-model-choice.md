# ADR 0001: Model Choice (Baseline Ranking)

## Status
Accepted

## Context
We need a baseline machine learning algorithm to score synthetic user-offer candidate pairs. The model must handle tabular data (continuous, categorical), train quickly locally, and provide probability estimates for pointwise ranking.

## Decision
We chose `HistGradientBoostingClassifier` from `scikit-learn` as the baseline model.

## Rationale
- **Performance:** Gradient boosting tree algorithms excel at tabular data with non-linear relationships. `HistGradientBoostingClassifier` is highly optimized and natively handles missing values and categorical features without excessive one-hot encoding logic.
- **Simplicity:** Keeps the stack lightweight (only requires scikit-learn) without bringing in external dependencies like XGBoost or LightGBM for the version 1 baseline.
- **Maintainability:** Easy to serialize as a `joblib` artifact and serve via FastAPI.

## Consequences
- Fast training times on the 100k+ row synthetic dataset.
- Does not inherently optimize for listwise metrics (like NDCG) during training, but serves well for pointwise scoring followed by rules-based reranking.