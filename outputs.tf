output "cloud_run_url" {
  value = google_cloud_run_service.news_hook.status[0].url
}

output "database_connection_name" {
  value = google_sql_database_instance.news_hook.connection_name
}

output "backend_url" {
  value = google_cloud_run_service.backend.status[0].url
}

output "database_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}