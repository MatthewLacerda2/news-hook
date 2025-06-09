locals {
  cloudbuild_service_account = "${var.project_id}@cloudbuild.gserviceaccount.com"
}

# Permissions needed by Cloud Build
resource "google_project_iam_member" "cloudbuild_permissions" {
  for_each = toset([
    "roles/run.admin",            # Deploy to Cloud Run
    "roles/iam.serviceAccountUser", # Use service accounts
    "roles/cloudbuild.builds.builder", # Create builds
    "roles/storage.admin",        # Access to Container Registry
    "roles/secretmanager.secretAccessor" # Access secrets
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${local.cloudbuild_service_account}"
} 