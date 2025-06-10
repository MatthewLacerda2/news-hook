resource "google_sql_database" "existing" {
  name     = "news_hook"
  instance = "news-hook-id"
}

resource "google_sql_user" "database_user" {
  name     = "news-hook-id"
  instance = "news-hook-id"
  password = var.database_password
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google-client-secret" {
  secret_id = "google-client-secret"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "jwt-secret" {
  secret_id = "jwt-secret"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://${google_sql_user.database_user.name}:${var.database_password}@/news_hook?host=/cloudsql/${var.project_id}:${var.region}:news-hook-id"
}

resource "google_secret_manager_secret_version" "google-client-secret" {
  secret      = google_secret_manager_secret.google-client-secret.id
  secret_data = var.google_client_secret
}

resource "google_secret_manager_secret_version" "jwt-secret" {
  secret      = google_secret_manager_secret.jwt-secret.id
  secret_data = var.jwt_secret
}
