# ===========================================
# IAM Module Outputs
# ===========================================

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.service_account.email
}

output "service_account_id" {
  description = "Service account ID"
  value       = google_service_account.service_account.id
}

output "service_account_name" {
  description = "Service account unique ID"
  value       = google_service_account.service_account.unique_id
}

output "service_account_member" {
  description = "Service account member string for IAM bindings"
  value       = "serviceAccount:${google_service_account.service_account.email}"
}
