# ===========================================
# Networking Module Outputs
# ===========================================

output "vpc_id" {
  description = "VPC network ID"
  value       = google_compute_network.vpc.id
}

output "vpc_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "vpc_self_link" {
  description = "VPC network self link"
  value       = google_compute_network.vpc.self_link
}

output "psa_connection_id" {
  description = "Private Service Access connection ID"
  value       = google_service_networking_connection.private_vpc_connection.id
}

output "connector_id" {
  description = "VPC connector ID"
  value       = google_vpc_access_connector.connector.id
}

output "connector_name" {
  description = "VPC connector name"
  value       = google_vpc_access_connector.connector.name
}

output "connector_self_link" {
  description = "VPC connector self link"
  value       = google_vpc_access_connector.connector.self_link
}
