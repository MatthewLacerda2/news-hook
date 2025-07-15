# Non-secret variables - can be hardcoded
variable "project_id" {
  description = "Google Cloud project ID"
  default     = "driven-actor-461001-j0"
}

variable "region" {
  description = "Google Cloud region"
  default     = "southamerica-east1"
}

variable "service_name" {
  description = "Cloud Run service name"
  default     = "newshook-tf"
}

variable "GOOGLE_REDIRECT_URI" {
  description = "Google OAuth redirect URI"
  default     = "http://127.0.0.1:8000/api/v1/auth/signup"
}

# Secret variables - should be managed securely
variable "DATABASE_URL" {
  description = "Database connection URL"
  sensitive   = true
}

variable "GOOGLE_REFRESH_TOKEN" {
  description = "Google OAuth refresh token"
  sensitive   = true
}

variable "SECRET_KEY" {
  description = "Application secret key"
  sensitive   = true
}

variable "TELEGRAM_BOT_TOKEN" {
  description = "Telegram bot authentication token"
  sensitive   = true
}
