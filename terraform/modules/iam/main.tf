# ===========================================
# IAM Module
# ===========================================
# Creates Service Account and assigns IAM roles

# Create Service Account
resource "google_service_account" "service_account" {
  project      = var.project_id
  account_id   = var.service_account_id
  display_name = var.service_account_display_name
  description  = var.service_account_description
}

# Assign IAM roles to the service account
resource "google_project_iam_member" "roles" {
  for_each = toset(var.roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# Grant Secret Manager access for DB password
resource "google_secret_manager_secret_iam_member" "db_password_access" {
  count = var.db_password_secret_id != null ? 1 : 0

  project   = var.project_id
  secret_id = var.db_password_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.service_account.email}"
}
