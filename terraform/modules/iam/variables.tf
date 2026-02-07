# ===========================================
# IAM Module Variables
# ===========================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "service_account_id" {
  description = "Service account ID"
  type        = string
  default     = "risk-analyzer-sa"
}

variable "service_account_display_name" {
  description = "Service account display name"
  type        = string
  default     = "Risk Analyzer Service Account"
}

variable "service_account_description" {
  description = "Service account description"
  type        = string
  default     = "Service account for Risk Analyzer Cloud Run services"
}

variable "roles" {
  description = "List of IAM roles to assign to the service account"
  type        = list(string)
  default = [
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/speech.client",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/redis.editor",
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
  ]
}

variable "db_password_secret_id" {
  description = "Secret Manager secret ID for DB password (optional)"
  type        = string
  default     = null
}
