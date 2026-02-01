# ===========================================
# Redis Module Variables
# ===========================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "instance_name" {
  description = "Redis instance name"
  type        = string
  default     = "risk-analyzer-redis"
}

variable "tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"
}

variable "memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "REDIS_7_0"
}

variable "connect_mode" {
  description = "Connection mode"
  type        = string
  default     = "PRIVATE_SERVICE_ACCESS"
}

variable "authorized_network" {
  description = "Authorized VPC network ID"
  type        = string
}

variable "auth_enabled" {
  description = "Enable Redis AUTH"
  type        = bool
  default     = true
}

variable "transit_encryption_mode" {
  description = "Transit encryption mode"
  type        = string
  default     = "DISABLED"
}

variable "labels" {
  description = "Labels to apply to the instance"
  type        = map(string)
  default     = {}
}
