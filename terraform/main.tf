# ===========================================
# Risk Analyzer - GCP Infrastructure
# ===========================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ===========================================
# Enable Required APIs
# ===========================================
module "apis" {
  source = "./modules/apis"

  project_id = var.project_id
}

# ===========================================
# Artifact Registry
# ===========================================
module "artifact_registry" {
  source = "./modules/artifact-registry"

  project_id    = var.project_id
  region        = var.region
  repository_id = var.artifact_registry_id

  depends_on = [module.apis]
}

# ===========================================
# Networking (VPC Connector)
# ===========================================
module "networking" {
  source = "./modules/networking"

  project_id     = var.project_id
  region         = var.region
  connector_name = var.vpc_connector_name
  ip_cidr_range  = var.vpc_connector_cidr

  depends_on = [module.apis]
}

# ===========================================
# Memorystore Redis
# ===========================================
module "redis" {
  source = "./modules/redis"

  project_id         = var.project_id
  region             = var.region
  instance_name      = var.redis_instance_name
  tier               = var.redis_tier
  memory_size_gb     = var.redis_memory_size_gb
  authorized_network = module.networking.vpc_id

  labels = var.labels

  # PSAが完了してからRedisを作成する必要がある
  depends_on = [module.apis, module.networking]
}

# ===========================================
# Cloud SQL PostgreSQL
# ===========================================
module "cloudsql" {
  source = "./modules/cloudsql"

  project_id          = var.project_id
  region              = var.region
  instance_name       = var.sql_instance_name
  tier                = var.sql_tier
  deletion_protection = var.sql_deletion_protection
  database_name       = var.database_name
  private_network     = module.networking.vpc_id
  ipv4_enabled        = false

  labels = var.labels

  # PSAが完了してからCloud SQLを作成する必要がある
  depends_on = [module.apis, module.networking]
}

# ===========================================
# Cloud Storage
# ===========================================
module "storage" {
  source = "./modules/storage"

  project_id  = var.project_id
  bucket_name = "${var.project_id}-${var.storage_bucket_suffix}"
  location    = var.region

  lifecycle_rules = [
    {
      action_type = "Delete"
      age         = var.storage_lifecycle_age
    }
  ]

  force_destroy = var.storage_force_destroy

  labels = var.labels

  depends_on = [module.apis]
}

# ===========================================
# IAM (Service Account)
# ===========================================
module "iam" {
  source = "./modules/iam"

  project_id            = var.project_id
  service_account_id    = var.service_account_id
  db_password_secret_id = module.cloudsql.db_password_secret_id

  depends_on = [module.apis, module.cloudsql]
}

# ===========================================
# Workload Identity Federation
# ===========================================
module "workload_identity" {
  source = "./modules/workload-identity"

  project_id         = var.project_id
  github_repository  = var.github_repository
  service_account_id = module.iam.service_account_id

  depends_on = [module.iam]
}
