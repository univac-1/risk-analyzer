# ===========================================
# Memorystore Redis Module
# ===========================================
# Creates Memorystore Redis instance

resource "google_redis_instance" "instance" {
  project        = var.project_id
  name           = var.instance_name
  region         = var.region
  tier           = var.tier
  memory_size_gb = var.memory_size_gb
  redis_version  = var.redis_version

  connect_mode       = var.connect_mode
  authorized_network = var.authorized_network

  auth_enabled            = var.auth_enabled
  transit_encryption_mode = var.transit_encryption_mode

  labels = var.labels

  lifecycle {
    prevent_destroy = false
  }
}
