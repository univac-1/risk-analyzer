# ===========================================
# Redis Module Outputs
# ===========================================

output "instance_name" {
  description = "Redis instance name"
  value       = google_redis_instance.instance.name
}

output "host" {
  description = "Redis host IP address"
  value       = google_redis_instance.instance.host
}

output "port" {
  description = "Redis port"
  value       = google_redis_instance.instance.port
}

output "current_location_id" {
  description = "Current location ID"
  value       = google_redis_instance.instance.current_location_id
}

output "auth_string" {
  description = "Redis AUTH string"
  value       = google_redis_instance.instance.auth_string
  sensitive   = true
}
