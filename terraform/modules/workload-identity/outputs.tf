# ===========================================
# Workload Identity Module Outputs
# ===========================================

output "pool_id" {
  description = "Workload Identity Pool ID"
  value       = google_iam_workload_identity_pool.pool.workload_identity_pool_id
}

output "pool_name" {
  description = "Workload Identity Pool resource name"
  value       = google_iam_workload_identity_pool.pool.name
}

output "provider_id" {
  description = "Workload Identity Provider ID"
  value       = google_iam_workload_identity_pool_provider.github.workload_identity_pool_provider_id
}

output "provider_name" {
  description = "Workload Identity Provider full resource name"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "project_number" {
  description = "GCP project number"
  value       = data.google_project.project.number
}
