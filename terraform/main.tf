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

# Cloud Run service
resource "google_cloud_run_service" "news_hook" {
  name     = "news-hook"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/news-hook"
        
        ports {
          container_port = 8080
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql+asyncpg://news-hook-id:${var.database_password}@${data.google_sql_database_instance.existing.public_ip_address}:5432/news_hook"
        }
        
        env {
          name  = "GOOGLE_CLIENT_ID"
          value = var.google_client_id
        }
        
        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.google_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "JWT_ISSUER"
          value = "newshook"
        }

        env {
          name  = "JWT_AUDIENCE"
          value = "agent_controller"
        }

        env {
          name = "SECRET_KEY"
          value_from {
            secret_key_ref {
              name = data.google_secret_manager_secret.jwt_secret.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "ACCESS_TOKEN_EXPIRE_MINUTES"
          value = "43200"
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Reference to existing Cloud SQL instance
data "google_sql_database_instance" "existing" {
  name = "news-hook-id"
}

# Reference existing database
data "google_sql_database" "existing" {
  name     = "news_hook"
  instance = data.google_sql_database_instance.existing.name
}

# Cloud Build trigger
resource "google_cloudbuild_trigger" "news_hook" {
  name = "news-hook-main"

  github {
    owner = var.github_owner
    name  = "news-hook"
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"
}

# IAM - Allow Cloud Run to access Cloud SQL
resource "google_project_iam_member" "cloud_run_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_cloud_run_service.news_hook.template[0].spec[0].service_account_name}"
}

# Allow unauthenticated access to Cloud Run
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.news_hook.location
  service  = google_cloud_run_service.news_hook.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

