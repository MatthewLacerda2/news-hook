terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "driven-actor-461001-j0"
}

variable "region" {
  description = "The default GCP region"
  type        = string
  default     = "southamerica-west1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "news-hook"
} 