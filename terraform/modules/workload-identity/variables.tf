# ===========================================
# Workload Identity Module Variables
# ===========================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "pool_id" {
  description = "Workload Identity Pool ID"
  type        = string
  default     = "github-pool"
}

variable "pool_display_name" {
  description = "Workload Identity Pool display name"
  type        = string
  default     = "GitHub Actions Pool"
}

variable "pool_description" {
  description = "Workload Identity Pool description"
  type        = string
  default     = "Workload Identity Pool for GitHub Actions"
}

variable "provider_id" {
  description = "Workload Identity Provider ID"
  type        = string
  default     = "github-provider"
}

variable "provider_display_name" {
  description = "Workload Identity Provider display name"
  type        = string
  default     = "GitHub Provider"
}

variable "attribute_condition" {
  description = "Attribute condition for the provider (optional, for restricting access)"
  type        = string
  default     = null
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}

variable "service_account_id" {
  description = "Service account ID to allow impersonation"
  type        = string
}
