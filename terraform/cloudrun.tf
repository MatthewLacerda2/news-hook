resource "google_cloud_run_service" "main" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/${var.service_name}:latest"
        
        env {
          name  = "DATABASE_URL"
          value = "postgresql+asyncpg://news-hook-id:l3nd4c3rd4@35.247.207.49:5432/news_hook"
        }
        
        env {
          name  = "GOOGLE_PROJECT_ID"
          value = var.project_id
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
          name  = "ACCESS_TOKEN_EXPIRE_MINUTES"
          value = "43200"
        }

        # Sensitive environment variables from Secret Manager
        env {
          name = "DATABASE_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.database_password.secret_id
              key  = "latest"
            }
          }
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
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
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

# Allow unauthenticated access to the service
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.main.name
  location = google_cloud_run_service.main.location
  role     = "roles/run.invoker"
  member   = "allUsers"
} 