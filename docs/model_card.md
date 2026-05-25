# Model Card: Bank Offer Feed Ranking (Baseline)

## 1. Model Details
- **Architecture:** `HistGradientBoostingClassifier` (scikit-learn).
- **Task:** Point-wise ranking classification.
- **Features:** 25 features spanning user demographics, macroeconomic indicators, offer attributes, and deterministic affinity scores.
- **Version:** v1 (Baseline)

## 2. Intended Use
- **Primary Use:** Rank candidate bank offers (credit card, savings, loans, etc.) for existing users within a synthetic demo application.
- **Out-of-Scope Uses:** Real financial decisioning, production regulatory compliance, dynamic pricing, or real-time online learning.

## 3. Training Data
- **Source:** Based on the UCI Bank Marketing dataset (`bank-additional-full.csv`).
- **Processing:** Includes synthetic generation of user-offer pairs (~101K examples) based on baseline dataset heuristics.
- **Excluded Features:** The `duration` field is strictly excluded from all training and inference pipelines. It is highly predictive but represents post-decision information (duration of the marketing call) and would cause data leakage for decision-time predictions.

## 4. Evaluation Metrics (Offline)
- **Classification:**
  - AUC: `0.815`
  - Log Loss: `0.271`
- **Ranking (Top-K=3):**
  - Precision@3: `0.089`
  - Recall@3: `0.106`
  - MAP@3: `0.110`
  - NDCG@3: `0.110`

*Note: Since offers are synthesized and labels are probabilistically assigned via heuristics, precision/recall metrics reflect offline ranking capability on synthetic targets rather than real-world conversion rates.*

## 5. Synthetic Label Caveats & Limitations
1. **Synthetic Bias:** The model's behavior is strongly conditioned on the deterministic heuristic assumptions used during pair and label generation.
2. **Cold Start Limitations:** Users without historical macroeconomic context or demographic alignment might receive sub-optimal default rankings.
3. **No Dynamic Updates:** Model is pre-compiled offline; it does not adjust on-the-fly to real-time feedback events in this iteration.