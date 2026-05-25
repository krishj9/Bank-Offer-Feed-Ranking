# AWS Deployment Guide

This guide covers two deployment patterns for Bank Offer Feed Ranking on AWS:

| Pattern | Best when | Idle cost (typical) |
|---------|-----------|---------------------|
| **[Option A: EC2](#option-a-ec2-single-instance)** | You want the simplest mirror of local dev, SSH access, or on-instance training | **~$0** if the instance is **stopped**; ~\$30/month if `t3.medium` runs 24/7 |
| **[Option B: Serverless](#option-b-serverless-low-traffic)** | Traffic is sparse (e.g. ~5 minutes/month) and you want pay-per-use API + static hosting | **Near $0** when idle (no EC2 hours; small S3/CloudFront + rare Lambda invocations) |

> **Scope:** Version 1 includes optional **Terraform** under `infra/terraform/` for the serverless stack (S3, ECR, Lambda, API Gateway, CloudFront). EC2 remains a manual procedure. Train ML **locally or in CI**, then publish artifacts and data to S3 (recommended for either option).

### Terraform (serverless)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply   # see README: two-phase apply when enable_lambda = false first
```

Details: [infra/terraform/README.md](../infra/terraform/README.md).

For **why** these patterns were chosen (Lambda container vs zip, ECS Fargate, SageMaker), see [Architecture choices](#architecture-choices-rationale).

---

## Architecture choices (rationale)

This project can run the same FastAPI + in-process `joblib` model on several AWS compute options. Version 1 documents **EC2** and **Lambda (container)**; Terraform implements the serverless path. The sections below explain trade-offs so you can pick or extend deployments (e.g. Fargate) without guessing.

### How the app runs everywhere

Regardless of host, the ranking path is the same:

1. Load eligible offers and build feature rows (`CandidateService`).
2. Transform with shared `FeatureBuilder` (same contract as training).
3. Score with `baseline_model.joblib` via `predict_proba` (or deterministic fallback if artifacts are missing).
4. Rerank, explain, return JSON.

Nothing in that flow **requires** EC2, Lambda, or SageMaker specifically—only a Python runtime, filesystem paths to artifacts/data, and (for production UI) HTTPS + CORS.

### EC2 (Option A)

| Pros | Cons |
|------|------|
| Simplest mirror of local dev (`uvicorn`, SSH, logs on disk) | You must **stop** the instance for ~$0 compute when idle |
| No cold starts while the VM is running | Not “serverless”; 24/7 `t3.medium` is ~\$30/month |
| Easy durable feedback JSONL on disk | You operate patching, security groups, and the OS |

**Chosen for v1 when:** you want minimal conceptual overhead, might train on the box, or need SSH debugging.

### Lambda with a container image (Option B default)

| Pros | Cons |
|------|------|
| **Near-zero idle cost** for sparse traffic (e.g. ~5 minutes/month) | **Cold starts** after idle (large image + sklearn import) |
| Pay per request + GB-second | Two-step deploy: push image to ECR, then create/update function |
| Same monorepo layout baked into the image as local/EC2 | Feedback to `/tmp` is **ephemeral** unless you add S3/EFS |

**Why a container, not a zip deployment?**

- Dependencies (**pandas**, **scikit-learn**, **pyarrow**) and the **joblib** artifact exceed practical **Lambda zip + layer** size and maintenance limits.
- A **container image** keeps one packaging story aligned with `pyproject.toml` and `infra/aws/serverless/Dockerfile`, instead of a separate slim Lambda requirements tree that can drift from training.
- **Mangum** wraps the existing FastAPI app; inference is still in-process `predict_proba`, not a separate inference service.

Zip Lambda remains valid for tiny handlers or externalized models; it is not the default for this sklearn baseline.

### ECS Fargate (not in v1 Terraform, but a strong alternative)

Fargate runs the **same Docker image** with a long-lived `uvicorn` process—often **simpler at runtime** than Lambda (load the model once per task, no API Gateway proxy event model).

| Pros | Cons |
|------|------|
| No Lambda cold start if a task is always running | **Idle cost**: a running task bills CPU/memory even with zero users |
| Natural fit for durable volumes (EFS) and feedback files | More IaC: cluster, service, task definition, ALB, often VPC |
| Same ECR image as Lambda container path | Scale-to-zero on Fargate needs extra design (not “free” idle by default) |

**Why v1 did not default to Fargate:**

- The target usage pattern is **minutes per month**; Fargate is a better fit for **steady or always-on** traffic unless you invest in scale-to-zero.
- The repo already splits “VM simplicity” (**EC2**) from “true scale-to-zero API” (**Lambda**). Fargate sits in the middle: more production-like than EC2, heavier than Lambda + API Gateway for a demo scope.
- **sklearn / joblib does not require Lambda**; Fargate was omitted to limit Terraform surface area, not because of technical incompatibility.

**When to prefer Fargate:** predictable latency, growing QPS, persistent feedback storage, or org standardization on ECS—reuse `infra/aws/serverless/Dockerfile` with `CMD` changed to `uvicorn` behind an ALB.

### SageMaker (not required for v1)

SageMaker helps with managed training pipelines, model registry, and dedicated inference endpoints at scale. This baseline is a small **HistGradientBoosting** model served inside FastAPI; **SageMaker adds cost and integration** (endpoint invoke or batch) without simplifying the demo. Train locally or in CI, publish `ml/artifacts/` to S3, and load in the API process—on EC2, Lambda, or Fargate.

### Summary decision matrix

| Pattern | Idle cost (typical) | Cold start | Ops complexity | In this repo |
|---------|---------------------|------------|----------------|--------------|
| EC2 (stopped when idle) | ~\$0 compute | None while running | Low | Option A (manual) |
| Lambda (container) | ~\$0 | Yes | Medium | Option B + Terraform |
| Lambda (zip) | ~\$0 | Yes | Medium–high (layers/size) | Not documented (deps too heavy) |
| ECS Fargate | Often > \$0 unless scaled to zero | Low if task is up | High | Future / custom |
| SageMaker endpoint | Endpoint hourly if provisioned | Low | High | Not used in v1 |

---

## Prerequisites (both options)

- **AWS account** with billing enabled.
- **IAM** user or role with rights for your chosen pattern (EC2 and S3, or Lambda, API Gateway, S3, CloudFront, ECR).
- **Region** (e.g. `us-east-1`).
- **Local prep** completed per [Local Installation Guide](install-local.md):
  - Raw CSV in `data/raw/bank-additional-full.csv`
  - `uv run python -m ml.data.run_pipeline`
  - `uv run python -m ml.data.run_synthetic`
  - `uv run python -m ml.training.train` (optional but recommended)

### Shared S3 layout (recommended)

Create one bucket (example: `bofr-demo-<account-id>`) and upload runtime assets:

```bash
export BOFR_BUCKET=bofr-demo-<account-id>
export AWS_REGION=us-east-1

aws s3 mb "s3://${BOFR_BUCKET}" --region "${AWS_REGION}"

aws s3 sync ml/artifacts/ "s3://${BOFR_BUCKET}/ml/artifacts/"
aws s3 cp data/processed/sample_users.json "s3://${BOFR_BUCKET}/data/processed/sample_users.json"
aws s3 cp data/synthetic/offers.csv "s3://${BOFR_BUCKET}/data/synthetic/offers.csv"
```

EC2 can download these on boot; the serverless container build can bake them in or sync at image build time (see Option B).

---

## Option A: EC2 single instance

Docker-free pattern that mirrors local architecture: FastAPI on port 8000, static frontend on port 80/5173.

### A.1 Launch EC2

1. AMI: Amazon Linux 2023 or Ubuntu 22.04.
2. Instance type:
   - **Inference + UI only:** `t3.small` or `t3.medium` (pull artifacts from S3).
   - **Train on the box:** `t3.medium` or larger.
3. Security group inbound:
   - `22` (SSH, restrict source IP)
   - `8000` (API)
   - `80` or `5173` (frontend), or terminate HTTPS at ALB later.

### A.2 Install and clone

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv nodejs npm git awscli
git clone <your-repo-url>
cd Bank-Offer-Feed-Ranking
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### A.3 Data and artifacts on the instance

**Preferred:** sync from S3 (no training on production VM):

```bash
aws s3 sync "s3://${BOFR_BUCKET}/ml/artifacts/" ml/artifacts/
aws s3 cp "s3://${BOFR_BUCKET}/data/processed/sample_users.json" data/processed/sample_users.json
aws s3 cp "s3://${BOFR_BUCKET}/data/synthetic/offers.csv" data/synthetic/offers.csv
```

**Alternative:** upload `bank-additional-full.csv` and run pipelines on EC2 (same commands as local install guide).

Attach an **IAM instance profile** with `s3:GetObject` on the bucket instead of long-lived access keys.

### A.4 Run services

**Backend:**

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use `systemd` or `pm2` for persistence. Set `CORS_ALLOWED_ORIGINS` if the UI is served from a different origin (see [CORS](#cors-frontend--api)).

**Frontend (production build):**

```bash
cd frontend
VITE_API_BASE_URL=http://<EC2_PUBLIC_IP>:8000 npm run build
npx serve -s dist -l 5173
```

Or serve `dist/` with Nginx on port 80.

### A.5 Cost control for low traffic (~5 min/month)

- **Stop** the instance when the demo is not in use (no compute charge while stopped; EBS storage still billed).
- Do **not** leave `t3.medium` running 24/7 unless you need always-on availability.
- Keep artifacts in S3 so a fresh instance can resync quickly.

### A.6 Verify

```bash
curl "http://<EC2_PUBLIC_IP>:8000/health"
curl "http://<EC2_PUBLIC_IP>:8000/api/v1/sample-users"
```

Open the UI at `http://<EC2_PUBLIC_IP>:5173` (or your Nginx URL).

---

## Option B: Serverless (low traffic)

Pay-per-use layout for infrequent access:

```text
Browser → CloudFront → S3 (React static build)
              ↓ API calls
         API Gateway (HTTP API) → Lambda (container, FastAPI + Mangum)
              ↓ reads
         S3 (artifacts, sample_users, offers) — baked into image or synced at build
```

**Packaging:** Lambda **container image** (see [Architecture choices](#architecture-choices-rationale)). Not zip—sklearn/pandas/joblib are too large and brittle for zip + layers.

**Trade-offs:**

| Topic | Serverless behavior |
|-------|---------------------|
| Cold start | First request after idle may take several seconds (model + sklearn load). Acceptable for ~5 min/month usage. |
| Feedback JSONL | Default path is ephemeral under `/tmp` on Lambda. Fine for demos; use S3/EFS later if you need durable feedback. |
| Training | Not on Lambda. Train locally/CI and publish to S3 or bake into the image. |

### B.1 Build the frontend

After API Gateway exists, set the API URL. For first deploy, use a placeholder and rebuild once the API URL is known.

```bash
cd frontend
VITE_API_BASE_URL=https://<api-id>.execute-api.<region>.amazonaws.com npm run build
aws s3 sync dist/ "s3://${BOFR_BUCKET}/web/" --delete
```

### B.2 Build and push the Lambda container

From the **repository root**, ensure `ml/artifacts/`, `data/processed/sample_users.json`, and `data/synthetic/offers.csv` exist (from local training/pipelines).

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export ECR_REPO=bofr-api

aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}" 2>/dev/null || true

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -f infra/aws/serverless/Dockerfile -t "${ECR_REPO}:latest" .
docker tag "${ECR_REPO}:latest" \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"
docker push "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"
```

The Dockerfile and handler live under `infra/aws/serverless/`.

### B.3 Create the Lambda function

Console or CLI (example CLI):

```bash
export IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"

aws lambda create-function \
  --function-name bofr-api \
  --package-type Image \
  --code ImageUri="${IMAGE_URI}" \
  --role arn:aws:iam::<account-id>:role/bofr-lambda-execution \
  --timeout 30 \
  --memory-size 2048 \
  --environment "Variables={
    APP_ENV=production,
    CORS_ALLOWED_ORIGINS=https://<cloudfront-domain>,
    MODEL_ARTIFACTS_DIR=/var/task/ml/artifacts,
    SAMPLE_USERS_PATH=/var/task/data/processed/sample_users.json,
    OFFERS_PATH=/var/task/data/synthetic/offers.csv,
    FEATURE_SCHEMA_PATH=/var/task/shared/contracts/feature_schema.json,
    RERANK_CONFIG_PATH=/var/task/backend/app/services/rerank_config.json,
    FEEDBACK_STORE_PATH=/tmp/feedback_events.jsonl
  }"
```

**IAM (`bofr-lambda-execution`):** basic `AWSLambdaBasicExecutionRole`. Add `s3:GetObject` only if you extend the app to sync from S3 at runtime instead of baking files into the image.

### B.4 API Gateway HTTP API

1. Create an **HTTP API**.
2. Integrate `ANY /{proxy+}` and `ANY /` routes to the Lambda (proxy integration).
3. Enable CORS on the API (allow your CloudFront origin, methods `GET,POST,OPTIONS`, headers `*` or explicit list).
4. Deploy to a stage (e.g. `prod`). Note the invoke URL: `https://<api-id>.execute-api.<region>.amazonaws.com`

Rebuild the frontend with that URL if you used a placeholder earlier.

### B.5 CloudFront for the SPA

1. Create a CloudFront distribution with origin = S3 bucket prefix `web/`.
2. Default root object: `index.html`.
3. Custom error response: **403 → /index.html, 200** (SPA client-side routing).
4. Optionally add a custom domain + ACM certificate.

Set Lambda `CORS_ALLOWED_ORIGINS` to the CloudFront URL (comma-separated if multiple).

### B.6 Verify serverless stack

```bash
export API_URL=https://<api-id>.execute-api.<region>.amazonaws.com
curl "${API_URL}/health"
curl "${API_URL}/api/v1/sample-users"
```

Open the CloudFront URL in a browser, select a user, and confirm rank + feedback calls succeed (check browser network tab for API URL and CORS).

### B.7 Serverless cost notes (~5 min/month)

- **Lambda:** charged per invocation + GB-second; negligible at minutes/month.
- **API Gateway:** per-million requests; negligible.
- **S3 + CloudFront:** cents for static assets and a few API calls.
- **ECR:** storage cost for one image (small).
- No always-on EC2 required.

---

## CORS (frontend ↔ API)

When the UI and API are on different hosts (CloudFront vs API Gateway, or S3 vs EC2), set:

```bash
export CORS_ALLOWED_ORIGINS=https://d111111abcdef8.cloudfront.net
```

The backend enables CORS middleware when this variable is non-empty (comma-separated list). EC2-only deployments on the same origin may leave it unset.

---

## Security

- Never commit AWS access keys. Use IAM roles (EC2 instance profile, Lambda execution role).
- Restrict security groups and CloudFront/WAF if the demo is private.
- Limit S3 bucket access with IAM and block public access except via CloudFront OAC/OAI.

---

## Choosing a deployment pattern

Quick picker (details in [Architecture choices](#architecture-choices-rationale)):

| Criterion | EC2 | Lambda (container) | ECS Fargate |
|-----------|-----|-------------------|-------------|
| Usage | SSH, on-box training, long sessions | ~minutes per month | Steady traffic or always-on API |
| Idle cost | ~\$0 if **stopped** | ~\$0 | Usually **>\$0** unless scaled to zero |
| Ops complexity | Lowest | Medium (ECR, API GW, CloudFront) | Highest (ECS, ALB, …) |
| Cold start | None while instance runs | Yes after idle | Low if tasks are running |
| Runtime | `uvicorn` on VM | Mangum + FastAPI | `uvicorn` in task (same image possible) |

**Neither EC2 nor Lambda requires SageMaker** for this baseline: both load `baseline_model.joblib` in the FastAPI process.

---

## Comparison to local install

Follow [install-local.md](install-local.md) for pipelines and training. AWS deployment only changes **where** artifacts and services run:

1. Publish `ml/artifacts/` + processed data to S3 (or bake into Lambda image).
2. Deploy API (EC2 uvicorn or Lambda).
3. Deploy UI (EC2 static serve or S3 + CloudFront).
4. Point `VITE_API_BASE_URL` at the API base URL.

---

## Scope caveats (v1)

- Not production HA: no multi-AZ autoscaling blueprint in-repo.
- No managed database; feedback is JSONL (ephemeral on Lambda `/tmp`).
- **Terraform** covers the serverless stack only (`infra/terraform/`); EC2 and ECS Fargate are manual or future work.
- For always-on production with strict SLAs, consider **ECS Fargate** or **ALB + EC2 autoscaling** instead of single-instance EC2 or cold-start Lambda—see [Architecture choices](#architecture-choices-rationale).
