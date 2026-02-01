# ===========================================
# Artifact Registry Module Variables
# ===========================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "repository_id" {
  description = "Repository ID"
  type        = string
  default     = "risk-analyzer"
}

variable "description" {
  description = "Repository description"
  type        = string
  default     = "Risk Analyzer Docker images"
}

variable "enable_cleanup_policy" {
  description = "Enable cleanup policy for old images"
  type        = bool
  default     = false
}

variable "cleanup_policy_dry_run" {
  description = "Run cleanup policy in dry-run mode"
  type        = bool
  default     = true
}

variable "cleanup_older_than" {
  description = "Delete images older than this duration (e.g., 2592000s = 30 days)"
  type        = string
  default     = "2592000s"
}
