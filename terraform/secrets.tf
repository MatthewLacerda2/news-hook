# Reference existing secrets
data "google_secret_manager_secret" "database_password" {
  secret_id = "database-password"
}

data "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
}

data "google_secret_manager_secret" "google_client_secret" {
  secret_id = "google-client-secret"
}
