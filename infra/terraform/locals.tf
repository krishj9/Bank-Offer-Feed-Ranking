locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )

  data_bucket_name = "${local.name_prefix}-data-${data.aws_caller_identity.current.account_id}"
  web_bucket_name  = "${local.name_prefix}-web-${data.aws_caller_identity.current.account_id}"
  ecr_repo_name    = "${local.name_prefix}-api"

  lambda_image_uri = "${aws_ecr_repository.api.repository_url}:${var.lambda_image_tag}"

  # Paths match infra/aws/serverless/Dockerfile (LAMBDA_TASK_ROOT = /var/task).
  lambda_task_root = "/var/task"

  cors_allowed_origins = (
    var.enable_cloudfront && var.enable_lambda
    ? "https://${aws_cloudfront_distribution.web[0].domain_name}"
    : var.cors_allowed_origins
  )
}
