# Example Terraform variables file - replace placeholders with your values

aws_bedrock_base_url = "https://bedrock-mantle.eu-north-1.api.aws/v1"
default_aws_region   = "eu-north-1"
project_id           = "PROJECT_ID_PLACEHOLDER"
project_name         = "twin"
environment          = "dev"
bedrock_model_id     = "amazon.nova-micro-v1:0"
lambda_timeout       = 300
api_throttle_burst_limit = 10
api_throttle_rate_limit  = 5
use_custom_domain        = false
root_domain              = ""

# PushOver (notifications)
push_over_user = "PUSHOVER_USER_KEY"
push_over_token = "PUSHOVER_TOKEN"

# Email (SMTP)
email_smtp_server = "smtp.gmail.com"
email_app_password = "EMAIL_APP_PASSWORD"
email_address = "YOUR_EMAIL@example.com"

# GitHub / MCP
github_mcp_token = "GITHUB_MCP_TOKEN"

# LLM / API keys
llm_model_id = "openai.gpt-oss-120b"
openai_api_key = "OPENAI_API_KEY"

aws_region = "eu-north-1"
use_s3 = true
