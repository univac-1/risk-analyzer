# ===========================================
# Terraform Backend Configuration
# ===========================================
# Store state in GCS bucket (created by bootstrap.sh)

terraform {
  backend "gcs" {
    bucket = "agentic-ai-hackathon-vol4-terraform-state"
    prefix = "terraform/state"
  }
}
