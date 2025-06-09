resource "google_cloudbuild_trigger" "main" {
  name        = "${var.service_name}-trigger"
  description = "Trigger for ${var.service_name} service"

  github {
    owner = "MatthewLacerda2"
    name  = "news-hook"
    push {
      branch = "^main$"
    }
  }

  substitutions = {
    _CLOUD_SQL_CONNECTION_NAME = "${var.project_id}:southamerica-west1:news-hook-db"
    _SERVICE_ACCOUNT          = "${var.project_id}@appspot.gserviceaccount.com"
  }

  filename = "cloudbuild.yaml"
}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${var.project_id}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${var.project_id}@cloudbuild.gserviceaccount.com"
} 