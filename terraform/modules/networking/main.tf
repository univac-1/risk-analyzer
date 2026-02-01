# ===========================================
# Networking Module
# ===========================================
# Creates VPC + Private Service Access + VPC Connector

# (1) VPC本体
resource "google_compute_network" "vpc" {
  project                 = var.project_id
  name                    = var.vpc_name
  auto_create_subnetworks = true
}

# (2) Private Service Access に必要な API
resource "google_project_service" "servicenetworking" {
  project            = var.project_id
  service            = "servicenetworking.googleapis.com"
  disable_on_destroy = false
}

# (3) PSA 用の予約レンジ
resource "google_compute_global_address" "private_service_range" {
  project       = var.project_id
  name          = "${var.vpc_name}-private-service-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# (4) PSA 接続本体
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]

  depends_on = [google_project_service.servicenetworking]
}

# (5) VPC Connector（Cloud RunなどServerlessサービス用）
resource "google_vpc_access_connector" "connector" {
  name          = var.connector_name
  project       = var.project_id
  region        = var.region
  ip_cidr_range = var.ip_cidr_range
  network       = google_compute_network.vpc.name

  min_instances = var.min_instances
  max_instances = var.max_instances
  machine_type  = var.machine_type

  depends_on = [google_compute_network.vpc]
}
