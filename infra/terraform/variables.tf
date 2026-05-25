variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short project prefix used in resource names."
  type        = string
  default     = "bofr"
}

variable "environment" {
  description = "Environment name (e.g. dev, demo, prod)."
  type        = string
  default     = "dev"
}

variable "lambda_memory_size" {
  description = "Lambda memory (MB) for the API container."
  type        = number
  default     = 2048
}

variable "lambda_timeout" {
  description = "Lambda timeout (seconds)."
  type        = number
  default     = 30
}

variable "lambda_image_tag" {
  description = "ECR image tag for the API Lambda container."
  type        = string
  default     = "latest"
}

variable "enable_lambda" {
  description = "Create Lambda + API Gateway. Set false for first apply before pushing a container image to ECR."
  type        = bool
  default     = true
}

variable "enable_cloudfront" {
  description = "Create CloudFront distribution for the static web bucket."
  type        = bool
  default     = true
}

variable "cors_allowed_origins" {
  description = "Comma-separated CORS origins for Lambda when CloudFront is disabled. Ignored when enable_cloudfront is true (origin is set from CloudFront domain)."
  type        = string
  default     = ""
}

variable "api_gateway_cors_allow_origins" {
  description = "CORS allow_origins for API Gateway HTTP API (browser preflight). Use ['*'] only for demos."
  type        = list(string)
  default     = ["*"]
}

variable "force_destroy_buckets" {
  description = "Allow Terraform to delete S3 buckets that still contain objects (demo only)."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Extra tags applied to all resources."
  type        = map(string)
  default     = {}
}
