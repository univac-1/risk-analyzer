# ===========================================
# APIs Module Variables
# ===========================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "apis" {
  description = "List of APIs to enable"
  type        = list(string)
  default = [
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "speech.googleapis.com",
    "videointelligence.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
  ]
}
