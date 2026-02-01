#!/bin/bash
# ===========================================
# GCP Infrastructure Setup Script
# ===========================================
# This script sets up the required GCP infrastructure for the Risk Analyzer application.
# Prerequisites: gcloud CLI installed and authenticated

set -e

# Configuration - Update these values
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-asia-northeast1}"
ZONE="${GCP_ZONE:-asia-northeast1-a}"

# Resource names
ARTIFACT_REPO="risk-analyzer"
VPC_CONNECTOR="risk-analyzer-connector"
REDIS_INSTANCE="risk-analyzer-redis"
SQL_INSTANCE="risk-analyzer-db"
STORAGE_BUCKET="${PROJECT_ID}-videos"
SERVICE_ACCOUNT="risk-analyzer-sa"

echo "========================================"
echo "GCP Infrastructure Setup for Risk Analyzer"
echo "========================================"
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set project
echo "[1/10] Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "[2/10] Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    vpcaccess.googleapis.com \
    compute.googleapis.com \
    speech.googleapis.com \
    videointelligence.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com

# Create Artifact Registry repository
echo "[3/10] Creating Artifact Registry repository..."
gcloud artifacts repositories create ${ARTIFACT_REPO} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Risk Analyzer Docker images" \
    || echo "Repository already exists"

# Create VPC connector for serverless services
echo "[4/10] Creating VPC connector..."
gcloud compute networks vpc-access connectors create ${VPC_CONNECTOR} \
    --region=${REGION} \
    --range=10.8.0.0/28 \
    || echo "VPC connector already exists"

# Create Memorystore Redis instance
echo "[5/10] Creating Memorystore Redis instance..."
gcloud redis instances create ${REDIS_INSTANCE} \
    --region=${REGION} \
    --tier=basic \
    --size=1 \
    --redis-version=redis_7_0 \
    --connect-mode=private-service-access \
    || echo "Redis instance already exists or is being created"

# Get Redis IP (may need to wait for creation)
echo "[6/10] Getting Redis IP address..."
REDIS_HOST=$(gcloud redis instances describe ${REDIS_INSTANCE} \
    --region=${REGION} \
    --format="value(host)" 2>/dev/null || echo "pending")
echo "Redis Host: ${REDIS_HOST}"

# Create Cloud SQL PostgreSQL instance
echo "[7/10] Creating Cloud SQL instance..."
gcloud sql instances create ${SQL_INSTANCE} \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=${REGION} \
    --root-password="${DB_PASSWORD:-$(openssl rand -base64 16)}" \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --availability-type=ZONAL \
    || echo "SQL instance already exists or is being created"

# Create database
echo "[8/10] Creating database..."
gcloud sql databases create video_risk_analyzer \
    --instance=${SQL_INSTANCE} \
    || echo "Database already exists"

# Create Cloud Storage bucket
echo "[9/10] Creating Cloud Storage bucket..."
gcloud storage buckets create gs://${STORAGE_BUCKET} \
    --location=${REGION} \
    --uniform-bucket-level-access \
    || echo "Bucket already exists"

# Set lifecycle policy for temporary files
cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
EOF
gcloud storage buckets update gs://${STORAGE_BUCKET} --lifecycle-file=/tmp/lifecycle.json

# Create Service Account for Cloud Run
echo "[10/10] Creating Service Account..."
gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
    --display-name="Risk Analyzer Service Account" \
    || echo "Service account already exists"

# Grant necessary permissions
SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/speech.client"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/videointelligence.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/aiplatform.user"

# Setup Workload Identity Federation for GitHub Actions
echo ""
echo "========================================"
echo "Setting up Workload Identity Federation..."
echo "========================================"

WIF_POOL="github-pool"
WIF_PROVIDER="github-provider"
GITHUB_REPO="${GITHUB_REPO:-owner/repo}"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create ${WIF_POOL} \
    --location="global" \
    --display-name="GitHub Actions Pool" \
    || echo "Pool already exists"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc ${WIF_PROVIDER} \
    --location="global" \
    --workload-identity-pool=${WIF_POOL} \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    || echo "Provider already exists"

# Get the full provider name
WIF_PROVIDER_FULL="projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${WIF_POOL}/providers/${WIF_PROVIDER}"

# Allow GitHub Actions to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding ${SA_EMAIL} \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')/locations/global/workloadIdentityPools/${WIF_POOL}/attribute.repository/${GITHUB_REPO}"

# Output summary
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Resources created:"
echo "  - Artifact Registry: ${ARTIFACT_REPO}"
echo "  - VPC Connector: ${VPC_CONNECTOR}"
echo "  - Redis Instance: ${REDIS_INSTANCE}"
echo "  - Cloud SQL Instance: ${SQL_INSTANCE}"
echo "  - Storage Bucket: ${STORAGE_BUCKET}"
echo "  - Service Account: ${SA_EMAIL}"
echo ""
echo "GitHub Actions Secrets to configure:"
echo "  GCP_PROJECT_ID=${PROJECT_ID}"
echo "  GCP_PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')"
echo "  WIF_PROVIDER=${WIF_PROVIDER_FULL}"
echo "  WIF_SERVICE_ACCOUNT=${SA_EMAIL}"
echo "  DB_CONNECTION_NAME=${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
echo "  DB_NAME=video_risk_analyzer"
echo "  DB_PASSWORD=<your-db-password>"
echo "  REDIS_HOST=${REDIS_HOST}"
echo "  GCS_BUCKET=${STORAGE_BUCKET}"
echo ""
echo "Note: Some resources may take a few minutes to fully provision."
