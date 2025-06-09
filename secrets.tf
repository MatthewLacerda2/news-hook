resource "google_secret_manager_secret" "database_password" {
  secret_id = "database-password"
  project   = var.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
  project   = var.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "google-client-secret"
  project   = var.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Grant Cloud Run access to secrets
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  for_each = toset([
    google_secret_manager_secret.database_password.id,
    google_secret_manager_secret.jwt_secret.id,
    google_secret_manager_secret.google_client_secret.id
  ])

  secret_id = each.key
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
}

# Note: The actual secret values should be set manually or through a secure CI/CD process
# terraform apply will only create the secret containers, not set their values 