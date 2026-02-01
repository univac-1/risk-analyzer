# ===========================================
# Risk Analyzer - Terraform Configuration
# ===========================================
# Update these values for your environment

# Core Settings
project_id = "agentic-ai-hackathon-vol4"
region     = "asia-northeast1"

labels = {
  app        = "risk-analyzer"
  managed_by = "terraform"
}

# Artifact Registry
artifact_registry_id = "risk-analyzer"

# Networking
vpc_connector_name = "risk-analyzer-connector"
vpc_connector_cidr = "10.8.0.0/28"

# Redis
redis_instance_name  = "risk-analyzer-redis"
redis_tier           = "BASIC"
redis_memory_size_gb = 1

# Cloud SQL
sql_instance_name       = "risk-analyzer-db"
sql_tier                = "db-f1-micro"
sql_deletion_protection = false
database_name           = "video_risk_analyzer"

# Cloud Storage
storage_bucket_suffix = "videos"
storage_lifecycle_age = 7
storage_force_destroy = true

# IAM
service_account_id = "risk-analyzer-sa"

# Workload Identity (Update with your GitHub repository)
github_repository = "univac-1/risk-analyzer"
