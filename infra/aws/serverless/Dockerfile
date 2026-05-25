# Lambda container image for FastAPI (build from repository root):
#   docker build -f infra/aws/serverless/Dockerfile -t bofr-api .
FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY ml ./ml
COPY shared ./shared
COPY data/processed/sample_users.json ./data/processed/sample_users.json
COPY data/synthetic/offers.csv ./data/synthetic/offers.csv

# Artifacts must exist before build (train locally or sync from S3 into ml/artifacts/).
COPY ml/artifacts/ ./ml/artifacts/

RUN pip install --no-cache-dir -e . mangum

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/backend
ENV APP_ENV=production
ENV MODEL_ARTIFACTS_DIR=${LAMBDA_TASK_ROOT}/ml/artifacts
ENV SAMPLE_USERS_PATH=${LAMBDA_TASK_ROOT}/data/processed/sample_users.json
ENV OFFERS_PATH=${LAMBDA_TASK_ROOT}/data/synthetic/offers.csv
ENV FEATURE_SCHEMA_PATH=${LAMBDA_TASK_ROOT}/shared/contracts/feature_schema.json
ENV RERANK_CONFIG_PATH=${LAMBDA_TASK_ROOT}/backend/app/services/rerank_config.json
ENV FEEDBACK_STORE_PATH=/tmp/feedback_events.jsonl

COPY infra/aws/serverless/lambda_handler.py ./

CMD ["lambda_handler.handler"]
