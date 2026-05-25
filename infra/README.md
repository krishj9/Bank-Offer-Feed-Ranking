# Infrastructure

Deployment assets for Bank Offer Feed Ranking on AWS.

## Layout

| Path | Description |
|------|-------------|
| [`terraform/`](terraform/) | Terraform for serverless stack (S3, ECR, Lambda, API Gateway, CloudFront, IAM) |
| [`aws/serverless/`](aws/serverless/) | Lambda container Dockerfile and Mangum handler |
| [`scripts/post-terraform-deploy.sh`](scripts/post-terraform-deploy.sh) | Build/push image and sync S3 after Terraform |

## Quick start (Terraform)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Phase 1: enable_lambda = false
terraform init && terraform apply

# Phase 2: from repo root
bash infra/scripts/post-terraform-deploy.sh
# Set enable_lambda = true in terraform.tfvars, then:
cd infra/terraform && terraform apply
```

Full steps: [terraform/README.md](terraform/README.md)

## Manual deploy

See [docs/install-aws.md](../docs/install-aws.md) for EC2 and serverless console/CLI instructions without Terraform.
