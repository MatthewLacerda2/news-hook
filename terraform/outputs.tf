output "cloud_run_url" {
  value = google_cloud_run_service.news_hook.status[0].url
}

output "database_connection_name" {
  value = data.google_sql_database_instance.existing.connection_name
}