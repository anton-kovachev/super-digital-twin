variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be one of: dev, test, prod."
  }
}

variable "bedrock_model_id" {
  description = "Bedrock model ID"
  type        = string
  default     = "amazon.nova-micro-v1:0"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 10
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 5
}

variable "use_custom_domain" {
  description = "Attach a custom domain to CloudFront"
  type        = bool
  default     = false
}

variable "root_domain" {
  description = "Apex domain name, e.g. mydomain.com"
  type        = string
  default     = ""
}

variable "aws_bedrock_base_url" {
  description = "AWS Bedrock base URL (e.g. https://bedrock-mantle.eu-north-1.api.aws/v1)"
  type        = string
}

variable "default_aws_region" {
  description = "Default AWS region for services"
  type        = string
}

variable "project_id" {
  description = "Project identifier (non-ARN project id)"
  type        = string
}

variable "push_over_user" {
  description = "Push Over user key"
  type        = string
}

variable "push_over_token" {
  description = "Push Over API token"
  type        = string
}

variable "email_smtp_server" {
  description = "SMTP server for sending emails"
  type        = string
}

variable "email_app_password" {
  description = "App password for the email account"
  type        = string
}

variable "email_address" {
  description = "Email address to send from"
  type        = string
}

variable "github_mcp_token" {
  description = "GitHub personal access token"
  type        = string
}

variable "llm_model_id" {
  description = "LLM model identifier to use"
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-north-1"
}

variable "use_s3" {
  description = "Flag to indicate whether to use S3 for storage"
  type        = bool
  default     = true
}