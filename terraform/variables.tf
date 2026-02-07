# ===========================================
# Risk Analyzer - Terraform Variables
# ===========================================

# ---------------------------------------------
# Core Settings
# ---------------------------------------------
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "labels" {
  description = "Common labels for all resources"
  type        = map(string)
  default     = {}
}

# ---------------------------------------------
# Artifact Registry
# ---------------------------------------------
variable "artifact_registry_id" {
  description = "Artifact Registry repository ID"
  type        = string
  default     = "risk-analyzer"
}

# ---------------------------------------------
# Networking
# ---------------------------------------------
variable "vpc_connector_name" {
  description = "VPC connector name"
  type        = string
  default     = "risk-analyzer-connector"
}

variable "vpc_connector_cidr" {
  description = "VPC connector CIDR range"
  type        = string
  default     = "10.8.0.0/28"
}

# ---------------------------------------------
# Redis
# ---------------------------------------------
variable "redis_instance_name" {
  description = "Redis instance name"
  type        = string
  default     = "risk-analyzer-redis"
}

variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# ---------------------------------------------
# Cloud SQL
# ---------------------------------------------
variable "sql_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "risk-analyzer-db"
}

variable "sql_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "sql_deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "video_risk_analyzer"
}

# ---------------------------------------------
# Cloud Storage
# ---------------------------------------------
variable "storage_bucket_suffix" {
  description = "Storage bucket name suffix (prepended with project ID)"
  type        = string
  default     = "videos"
}

variable "storage_lifecycle_age" {
  description = "Days before objects are deleted"
  type        = number
  default     = 7
}

variable "storage_force_destroy" {
  description = "Force destroy bucket even if not empty"
  type        = bool
  default     = true
}

# ---------------------------------------------
# IAM
# ---------------------------------------------
variable "service_account_id" {
  description = "Service account ID"
  type        = string
  default     = "risk-analyzer-sa"
}

# ---------------------------------------------
# Workload Identity
# ---------------------------------------------
variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}
