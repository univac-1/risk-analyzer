# ===========================================
# Risk Analyzer - Terraform Outputs
# ===========================================

# ---------------------------------------------
# Artifact Registry
# ---------------------------------------------
output "artifact_registry_url" {
  description = "Artifact Registry URL for Docker push/pull"
  value       = module.artifact_registry.repository_url
}

# ---------------------------------------------
# Networking
# ---------------------------------------------
output "vpc_connector_id" {
  description = "VPC connector ID for Cloud Run"
  value       = module.networking.connector_id
}

# ---------------------------------------------
# Redis
# ---------------------------------------------
output "redis_host" {
  description = "Redis host IP"
  value       = module.redis.host
}

output "redis_port" {
  description = "Redis port"
  value       = module.redis.port
}

# ---------------------------------------------
# Cloud SQL
# ---------------------------------------------
output "sql_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloudsql.connection_name
}

output "sql_database_name" {
  description = "Database name"
  value       = module.cloudsql.database_name
}

output "sql_db_user" {
  description = "Database user"
  value       = module.cloudsql.db_user
}

output "sql_db_password_secret" {
  description = "Secret Manager secret for DB password"
  value       = module.cloudsql.db_password_secret_name
}

# ---------------------------------------------
# Cloud Storage
# ---------------------------------------------
output "storage_bucket_name" {
  description = "Storage bucket name"
  value       = module.storage.bucket_name
}

# ---------------------------------------------
# IAM
# ---------------------------------------------
output "service_account_email" {
  description = "Service account email"
  value       = module.iam.service_account_email
}

# ---------------------------------------------
# Workload Identity
# ---------------------------------------------
output "workload_identity_provider" {
  description = "Workload Identity Provider name for GitHub Actions"
  value       = module.workload_identity.provider_name
}

output "project_number" {
  description = "GCP project number"
  value       = module.workload_identity.project_number
}

# ---------------------------------------------
# GitHub Actions Secrets (formatted for easy copy)
# ---------------------------------------------
output "github_actions_secrets" {
  description = "Values to set as GitHub Actions secrets"
  value = {
    GCP_PROJECT_ID       = var.project_id
    GCP_PROJECT_NUMBER   = module.workload_identity.project_number
    WIF_PROVIDER         = module.workload_identity.provider_name
    WIF_SERVICE_ACCOUNT  = module.iam.service_account_email
    DB_CONNECTION_NAME   = module.cloudsql.connection_name
    DB_NAME              = module.cloudsql.database_name
    DB_USER              = module.cloudsql.db_user
    DB_PASSWORD_SECRET   = module.cloudsql.db_password_secret_name
    REDIS_HOST           = module.redis.host
    GCS_BUCKET           = module.storage.bucket_name
    ARTIFACT_REGISTRY    = module.artifact_registry.repository_url
  }
}
