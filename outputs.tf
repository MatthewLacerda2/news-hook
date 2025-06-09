output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.main.status[0].url
}

output "cloud_sql_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = "${var.project_id}:${var.region}:${var.cloud_sql_instance_name}"
}

output "cloud_build_trigger_id" {
  description = "The ID of the Cloud Build trigger"
  value       = google_cloudbuild_trigger.main.trigger_id
}

output "service_account" {
  description = "The service account used by Cloud Run"
  value       = "${var.project_id}@appspot.gserviceaccount.com"
}

output "secret_manager_secrets" {
  description = "The names of the created secrets in Secret Manager"
  value = [
    google_secret_manager_secret.database_password.name,
    google_secret_manager_secret.jwt_secret.name,
    google_secret_manager_secret.google_client_secret.name
  ]
} 