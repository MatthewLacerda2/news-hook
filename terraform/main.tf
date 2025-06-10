resource "google_cloud_run_service" "news_hook" {
  name     = "newshook"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/news-hook/newshook:2e7075c870f0ff2ba0584e0a33d213fbd86e9496"
        
        env_from {
          secret_ref {
            local_object_reference {
              name = google_secret_manager_secret.database_url.name
            }
          }
        }
        
        env {
          name  = "GOOGLE_CLIENT_ID"
          value = var.google_client_id
        }
        
        env {
          name  = "GOOGLE_CLIENT_SECRET"
          value = var.google_client_secret
        }
        
        env {
          name  = "JWT_SECRET"
          value = var.jwt_secret
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.news_hook.name
  location = google_cloud_run_service.news_hook.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

import {
  id = "locations/${var.region}/namespaces/${var.project_id}/services/newshook"
  to = google_cloud_run_service.news_hook
}