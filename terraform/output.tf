output "cloud_run_url" {
  value = google_cloud_run_service.news_hook.status[0].url
}
