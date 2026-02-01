# ===========================================
# Artifact Registry Module
# ===========================================
# Creates Docker repository for container images

resource "google_artifact_registry_repository" "repository" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  description   = var.description
  format        = "DOCKER"

  cleanup_policy_dry_run = var.cleanup_policy_dry_run

  dynamic "cleanup_policies" {
    for_each = var.enable_cleanup_policy ? [1] : []
    content {
      id     = "delete-old-images"
      action = "DELETE"
      condition {
        older_than = var.cleanup_older_than
      }
    }
  }
}
