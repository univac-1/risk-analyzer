# ===========================================
# Networking Module Variables
# ===========================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "vpc_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "risk-analyzer-vpc"
}

variable "connector_name" {
  description = "Name of the VPC connector"
  type        = string
  default     = "risk-analyzer-connector"
}

variable "ip_cidr_range" {
  description = "IP CIDR range for the connector"
  type        = string
  default     = "10.8.0.0/28"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type for connector instances"
  type        = string
  default     = "e2-micro"
}
