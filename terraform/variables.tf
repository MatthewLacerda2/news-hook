variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The region to deploy resources to"
  type        = string
}

variable "db_tier" {
  description = "The machine type for the Cloud SQL instance"
  type        = string
}

variable "github_owner" {
  description = "The GitHub repository owner"
  type        = string
}

variable "database_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth2 Client ID"
  type        = string
}

variable "google_client_secret" {
  description = "Google OAuth2 Client Secret"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "Secret key for JWT tokens"
  type        = string
  sensitive   = true
}
