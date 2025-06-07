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
            name = "PORT"
            value = "8080"
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql+asyncpg://${google_sql_user.news_hook.name}:${var.database_password}@${google_sql_database_instance.news_hook.private_ip_address}:5432/${google_sql_database.news_hook.name}"
        }
        
        env {
          name  = "GOOGLE_CLIENT_ID"
          value = var.google_client_id
        }
        
        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_secret.secret_id
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
              name = google_secret_manager_secret.jwt_secret.secret_id
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

# Cloud SQL instance
resource "google_sql_database_instance" "news_hook" {
  name             = "news-hook-db"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  settings {
    tier = var.db_tier

    backup_configuration {
      enabled = true
      start_time = "04:00"
    }

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name = "all"
        value = "0.0.0.0/0"
      }
    }
  }
}

# Cloud SQL database
resource "google_sql_database" "news_hook" {
  name     = "news_hook"
  instance = google_sql_database_instance.news_hook.name
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

# Add database user
resource "google_sql_user" "news_hook" {
  name     = "news-hook-id"
  instance = google_sql_database_instance.news_hook.name
  password = var.database_password
}