provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloudbuild_trigger" "news_hook" {
  name        = "news-hook-tf-trigger"
  description = "Builds and deploys news-hook-tf from GitHub main branch"

  github {
    owner = "MatthewLacerda2"
    name  = "news-hook"
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"
}

resource "google_cloud_run_service" "news_hook" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/${var.service_name}:latest"
        env {
          name  = "DATABASE_URL"
          value = var.DATABASE_URL
        }
        env {
          name  = "GOOGLE_REDIRECT_URI"
          value = var.GOOGLE_REDIRECT_URI
        }
        env {
          name  = "GOOGLE_REFRESH_TOKEN"
          value = var.GOOGLE_REFRESH_TOKEN
        }
        env {
          name  = "SECRET_KEY"
          value = var.SECRET_KEY
        }
        env {
          name  = "TELEGRAM_BOT_TOKEN"
          value = var.TELEGRAM_BOT_TOKEN
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "noauth" {
  location        = google_cloud_run_service.news_hook.location
  project         = var.project_id
  service         = google_cloud_run_service.news_hook.name
  role            = "roles/run.invoker"
  member          = "allUsers"
}
