# Terraform — Bank Offer Feed Ranking (AWS serverless)

Provisions the **Option B (serverless)** stack from [docs/install-aws.md](../../docs/install-aws.md):

| Resource | Purpose |
|----------|---------|
| S3 `*-data-*` | ML artifacts + processed data (`aws s3 sync` from local) |
| S3 `*-web-*` | React production build (`dist/`) |
| ECR | Lambda container image for FastAPI |
| Lambda | API (`infra/aws/serverless/Dockerfile`) |
| API Gateway (HTTP API) | Public HTTPS API for the UI |
| CloudFront | SPA hosting with OAC → S3 web bucket |
| IAM | Lambda execution role + S3 read on data bucket |

EC2 is **not** managed here; use the manual EC2 section in `install-aws.md` or extend this module later.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.5
- AWS CLI configured (`aws sts get-caller-identity`)
- Docker (to build/push the Lambda image)
- Local data/artifacts from [install-local.md](../../docs/install-local.md)

## Two-phase apply (Lambda container image)

Lambda requires an image in ECR before the function can be created.

### Phase 1 — foundation (no Lambda)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Ensure: enable_lambda = false

terraform init
terraform plan
terraform apply
```

Note outputs: `data_bucket_name`, `web_bucket_name`, `ecr_repository_url`.

### Phase 2 — build, push, enable Lambda

From the **repository root**:

```bash
cd infra/terraform
export AWS_REGION=$(terraform output -raw aws_region)
export ECR_URL=$(terraform output -raw ecr_repository_url)
export IMAGE_TAG=latest

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_URL}"

docker build -f infra/aws/serverless/Dockerfile -t "${ECR_URL}:${IMAGE_TAG}" .
docker push "${ECR_URL}:${IMAGE_TAG}"
```

Set `enable_lambda = true` in `terraform.tfvars`, then:

```bash
terraform apply
```

Or update code only:

```bash
aws lambda update-function-code \
  --function-name "$(terraform output -raw lambda_function_name)" \
  --image-uri "$(terraform output -raw lambda_image_uri)" \
  --region "${AWS_REGION}"
```

### Phase 3 — publish data and UI

```bash
# Data bucket
aws s3 sync ml/artifacts/ "s3://$(terraform output -raw data_bucket_name)/ml/artifacts/"
aws s3 cp data/processed/sample_users.json "s3://$(terraform output -raw data_bucket_name)/data/processed/sample_users.json"
aws s3 cp data/synthetic/offers.csv "s3://$(terraform output -raw data_bucket_name)/data/synthetic/offers.csv"

# Frontend
cd frontend
VITE_API_BASE_URL="$(cd ../infra/terraform && terraform output -raw api_gateway_url)" npm run build
aws s3 sync dist/ "s3://$(cd ../infra/terraform && terraform output -raw web_bucket_name)/" --delete
```

Open `terraform output -raw cloudfront_url` in a browser.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `enable_lambda` | `true` | Create Lambda + API Gateway |
| `enable_cloudfront` | `true` | CloudFront + web bucket policy |
| `lambda_image_tag` | `latest` | ECR tag for API image |
| `force_destroy_buckets` | `true` | Empty buckets on `terraform destroy` (demo) |

See `variables.tf` for the full list.

## Outputs

```bash
terraform output
```

Key outputs: `api_gateway_url`, `cloudfront_url`, `data_bucket_name`, `web_bucket_name`, `ecr_repository_url`, `deploy_commands`.

## Helper script

From repo root (after phase 1 apply):

```bash
bash infra/scripts/post-terraform-deploy.sh
```

## Destroy

```bash
cd infra/terraform
terraform destroy
```

Empty ECR images and S3 objects first if `force_destroy_buckets = false`.

## State

No remote backend is configured. For teams, add an S3 + DynamoDB backend in `versions.tf`.
