# Decisions

- **Data Validation**: We decided to use basic pandas and JSON schema validation for the raw data ingestion rather than introducing heavy dependencies like Pandera or Pydantic at the data layer, keeping the pipeline simple and aligned with the JSON contract.
- **Target Mapping**: The target column 'y' is mapped from "yes"/"no" to 1/0 during preprocessing for easier downstream modeling.
- **Sample Users**: We extract 10 sample users using stratified sampling (when possible) to ensure a mix of positive and negative examples for the demo UI.
- **Offer Eligibility Rules**: Modeled `eligibility_rules` as an object in the JSON schema to allow structured rules (like min_age, job_types) which can be more easily processed by rule engines than raw strings.
- **Feature Schema Scope**: For T-016, we formalized `month` and `day_of_week` as `context_features` rather than `user_features` since they act as contextual indicators during inference, even though they originate from the user dataset. `duration` is explicitly excluded from the schema to prevent data leakage.
- **Feedback Storage (T-029)**: Selected **JSONL** for Wave 3 feedback persistence (`data/processed/feedback_events.jsonl`) to keep local development simple and append-friendly while preserving all required fields (`request_id`, `user_id`, `offer_id`, `action_type`, `timestamp`, `model_version`, `score`, `rank_position`).
- **Product Metrics Storage (T-042)**: Reused the existing JSONL event stream for both ranking impressions (`event_type=impression`, `action_type=viewed`) and explicit feedback (`event_type=feedback`) so metrics reports can be derived from one append-only source without adding a separate counter store.
