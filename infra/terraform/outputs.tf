output "aws_region" {
  description = "Deployed AWS region."
  value       = var.aws_region
}

output "data_bucket_name" {
  description = "S3 bucket for ML artifacts and processed data (sync from local)."
  value       = aws_s3_bucket.data.bucket
}

output "data_bucket_arn" {
  description = "ARN of the data S3 bucket."
  value       = aws_s3_bucket.data.arn
}

output "web_bucket_name" {
  description = "S3 bucket for frontend static files (sync dist/ here)."
  value       = aws_s3_bucket.web.bucket
}

output "ecr_repository_url" {
  description = "ECR repository URL (without tag)."
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name."
  value       = aws_ecr_repository.api.name
}

output "lambda_image_uri" {
  description = "Full image URI Terraform expects for Lambda."
  value       = local.lambda_image_uri
}

output "lambda_function_name" {
  description = "Lambda function name (null if enable_lambda is false)."
  value       = var.enable_lambda ? aws_lambda_function.api[0].function_name : null
}

output "api_gateway_url" {
  description = "HTTP API invoke URL for VITE_API_BASE_URL."
  value       = var.enable_lambda ? aws_apigatewayv2_api.http[0].api_endpoint : null
}

output "cloudfront_url" {
  description = "HTTPS URL for the SPA (null if CloudFront disabled)."
  value       = var.enable_cloudfront ? "https://${aws_cloudfront_distribution.web[0].domain_name}" : null
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name."
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.web[0].domain_name : null
}

output "cors_allowed_origins_lambda" {
  description = "CORS_ALLOWED_ORIGINS set on Lambda."
  value       = var.enable_lambda ? local.cors_allowed_origins : null
}

output "deploy_commands" {
  description = "Suggested post-terraform commands (run from repository root)."
  value = <<-EOT
    # 1) Upload runtime data to S3
    aws s3 sync ml/artifacts/ s3://${aws_s3_bucket.data.bucket}/ml/artifacts/
    aws s3 cp data/processed/sample_users.json s3://${aws_s3_bucket.data.bucket}/data/processed/sample_users.json
    aws s3 cp data/synthetic/offers.csv s3://${aws_s3_bucket.data.bucket}/data/synthetic/offers.csv

    # 2) Build and push Lambda image
    aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.api.repository_url}
    docker build -f infra/aws/serverless/Dockerfile -t ${aws_ecr_repository.api.repository_url}:${var.lambda_image_tag} .
    docker push ${aws_ecr_repository.api.repository_url}:${var.lambda_image_tag}

    # 3) Update Lambda to new image (if already created)
    aws lambda update-function-code --function-name ${var.enable_lambda ? aws_lambda_function.api[0].function_name : "${local.name_prefix}-api"} --image-uri ${local.lambda_image_uri} --region ${var.aws_region}

    # 4) Build and publish frontend
    cd frontend && VITE_API_BASE_URL=${var.enable_lambda ? aws_apigatewayv2_api.http[0].api_endpoint : "https://<api-gateway-url>"} npm run build
    aws s3 sync dist/ s3://${aws_s3_bucket.web.bucket}/ --delete
  EOT
}
