variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The default GCP region"
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
}

variable "database_name" {
  description = "The name of the database"
  type        = string
}

variable "database_user" {
  description = "The database user"
  type        = string
}

variable "cloud_sql_instance_name" {
  description = "The name of the Cloud SQL instance"
  type        = string
}

variable "github_owner" {
  description = "The GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "The GitHub repository name"
  type        = string
}

variable "min_scale" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_scale" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "512Mi"
} 