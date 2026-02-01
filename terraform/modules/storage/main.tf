# ===========================================
# Cloud Storage Module
# ===========================================
# Creates Cloud Storage bucket with lifecycle policy

resource "google_storage_bucket" "bucket" {
  project  = var.project_id
  name     = var.bucket_name
  location = var.location

  storage_class               = var.storage_class
  uniform_bucket_level_access = var.uniform_bucket_level_access
  public_access_prevention    = var.public_access_prevention

  force_destroy = var.force_destroy

  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules
    content {
      action {
        type          = lifecycle_rule.value.action_type
        storage_class = lookup(lifecycle_rule.value, "storage_class", null)
      }
      condition {
        age                   = lookup(lifecycle_rule.value, "age", null)
        created_before        = lookup(lifecycle_rule.value, "created_before", null)
        with_state            = lookup(lifecycle_rule.value, "with_state", null)
        matches_storage_class = lookup(lifecycle_rule.value, "matches_storage_class", null)
        num_newer_versions    = lookup(lifecycle_rule.value, "num_newer_versions", null)
      }
    }
  }

  versioning {
    enabled = var.versioning_enabled
  }

  labels = var.labels
}

# Optional: Set CORS configuration for web access
resource "google_storage_bucket" "cors" {
  count = var.enable_cors ? 1 : 0

  project  = var.project_id
  name     = "${var.bucket_name}-cors"
  location = var.location

  cors {
    origin          = var.cors_origins
    method          = var.cors_methods
    response_header = var.cors_response_headers
    max_age_seconds = var.cors_max_age_seconds
  }

  labels = var.labels
}
