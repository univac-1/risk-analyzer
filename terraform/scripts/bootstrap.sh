#!/bin/bash
# ===========================================
# Terraform State Bucket Bootstrap Script
# ===========================================
# Creates GCS bucket for Terraform state management
# Run this BEFORE terraform init

set -e

# Usage check
if [ $# -lt 1 ]; then
    echo "Usage: $0 <project-id>"
    echo "  Example: $0 my-gcp-project"
    exit 1
fi

PROJECT_ID=$1
REGION="${GCP_REGION:-asia-northeast1}"

BUCKET_NAME="${PROJECT_ID}-terraform-state"

echo "========================================"
echo "Terraform State Bucket Bootstrap"
echo "========================================"
echo "Project ID: ${PROJECT_ID}"
echo "Bucket: ${BUCKET_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set project
echo "[1/4] Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable Cloud Storage API
echo "[2/4] Enabling Cloud Storage API..."
gcloud services enable storage.googleapis.com

# Create bucket if not exists
echo "[3/4] Creating state bucket..."
if gcloud storage buckets describe gs://${BUCKET_NAME} > /dev/null 2>&1; then
    echo "Bucket already exists: ${BUCKET_NAME}"
else
    gcloud storage buckets create gs://${BUCKET_NAME} \
        --location=${REGION} \
        --uniform-bucket-level-access \
        --public-access-prevention
    echo "Bucket created: ${BUCKET_NAME}"
fi

# Enable versioning for state file protection
echo "[4/4] Enabling versioning..."
gcloud storage buckets update gs://${BUCKET_NAME} --versioning

echo ""
echo "========================================"
echo "Bootstrap Complete!"
echo "========================================"
echo ""
echo "State bucket: gs://${BUCKET_NAME}"
echo ""
echo "Next steps:"
echo "  1. Update terraform/backend.tf with the bucket name"
echo "  2. Update terraform/terraform.tfvars with your project_id"
echo "  3. Run the following commands:"
echo "     cd .."
echo "     terraform init"
echo "     terraform plan"
echo ""
