resource "aws_cloudwatch_log_group" "api" {
  count             = var.enable_lambda ? 1 : 0
  name              = "/aws/lambda/${local.name_prefix}-api"
  retention_in_days = 14
}

resource "aws_lambda_function" "api" {
  count = var.enable_lambda ? 1 : 0

  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.lambda[0].arn
  package_type  = "Image"
  image_uri     = local.lambda_image_uri

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  environment {
    variables = {
      APP_ENV              = var.environment
      CORS_ALLOWED_ORIGINS = local.cors_allowed_origins
      MODEL_ARTIFACTS_DIR  = "${local.lambda_task_root}/ml/artifacts"
      SAMPLE_USERS_PATH    = "${local.lambda_task_root}/data/processed/sample_users.json"
      OFFERS_PATH          = "${local.lambda_task_root}/data/synthetic/offers.csv"
      FEATURE_SCHEMA_PATH  = "${local.lambda_task_root}/shared/contracts/feature_schema.json"
      RERANK_CONFIG_PATH   = "${local.lambda_task_root}/backend/app/services/rerank_config.json"
      FEEDBACK_STORE_PATH  = "/tmp/feedback_events.jsonl"
      DATA_BUCKET_NAME     = aws_s3_bucket.data.bucket
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.api,
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_s3_read,
  ]

  tags = {
    Name = "${local.name_prefix}-api"
  }
}
