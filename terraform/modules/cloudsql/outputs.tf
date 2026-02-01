# ===========================================
# Cloud SQL Module Outputs
# ===========================================

output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.instance.name
}

output "connection_name" {
  description = "Cloud SQL connection name (project:region:instance)"
  value       = google_sql_database_instance.instance.connection_name
}

output "private_ip_address" {
  description = "Private IP address"
  value       = google_sql_database_instance.instance.private_ip_address
}

output "public_ip_address" {
  description = "Public IP address"
  value       = google_sql_database_instance.instance.public_ip_address
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "db_user" {
  description = "Database user name"
  value       = google_sql_user.user.name
}

output "db_password_secret_id" {
  description = "Secret Manager secret ID for database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "db_password_secret_name" {
  description = "Secret Manager secret resource name"
  value       = google_secret_manager_secret.db_password.name
}
