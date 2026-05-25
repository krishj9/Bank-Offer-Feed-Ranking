#!/usr/bin/env bash
# Post-Terraform deploy: push Lambda image, sync S3 data/web, optional terraform re-apply.
# Usage (from repository root):
#   bash infra/scripts/post-terraform-deploy.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TF_DIR="${ROOT_DIR}/infra/terraform"

cd "${TF_DIR}"
command -v terraform >/dev/null || { echo "terraform not found"; exit 1; }
command -v docker >/dev/null || { echo "docker not found"; exit 1; }
command -v aws >/dev/null || { echo "aws CLI not found"; exit 1; }

AWS_REGION="$(terraform output -raw aws_region)"
ECR_URL="$(terraform output -raw ecr_repository_url)"
IMAGE_TAG="$(terraform output -raw lambda_image_uri | awk -F: '{print $NF}')"
DATA_BUCKET="$(terraform output -raw data_bucket_name)"
WEB_BUCKET="$(terraform output -raw web_bucket_name)"
API_URL="$(terraform output -raw api_gateway_url 2>/dev/null || true)"

echo "==> ECR login (${AWS_REGION})"
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_URL%%/*}"

echo "==> Docker build & push"
cd "${ROOT_DIR}"
docker build -f infra/aws/serverless/Dockerfile -t "${ECR_URL}:${IMAGE_TAG}" .
docker push "${ECR_URL}:${IMAGE_TAG}"

FN="$(terraform -chdir="${TF_DIR}" output -raw lambda_function_name 2>/dev/null || true)"
if [[ -n "${FN}" && "${FN}" != "null" ]]; then
  echo "==> Update Lambda image: ${FN}"
  aws lambda update-function-code \
    --function-name "${FN}" \
    --image-uri "${ECR_URL}:${IMAGE_TAG}" \
    --region "${AWS_REGION}" >/dev/null
else
  echo "==> Lambda not deployed yet. Set enable_lambda=true in terraform.tfvars and run: terraform apply"
fi

echo "==> Sync data bucket"
aws s3 sync ml/artifacts/ "s3://${DATA_BUCKET}/ml/artifacts/"
aws s3 cp data/processed/sample_users.json "s3://${DATA_BUCKET}/data/processed/sample_users.json"
aws s3 cp data/synthetic/offers.csv "s3://${DATA_BUCKET}/data/synthetic/offers.csv"

if [[ -z "${API_URL}" || "${API_URL}" == "null" ]]; then
  echo "==> Skip frontend build (api_gateway_url not available)"
  exit 0
fi

echo "==> Build & sync frontend (API: ${API_URL})"
cd "${ROOT_DIR}/frontend"
VITE_API_BASE_URL="${API_URL}" npm run build
aws s3 sync dist/ "s3://${WEB_BUCKET}/" --delete

echo "==> Done. UI: $(terraform -chdir="${TF_DIR}" output -raw cloudfront_url 2>/dev/null || echo "enable CloudFront")"
