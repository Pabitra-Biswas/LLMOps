#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/setup_gcp.sh [PROJECT_ID] [REGION]
# Optional env flags:
#   SKIP_CLUSTER=1    skip creating GKE cluster
#   SKIP_AR=1         skip creating Artifact Registry repo
#   SKIP_BUCKET=1     skip creating GCS bucket
#   SKIP_KEY=1        skip creating/downloading service account key

# Default values set for your project
PROJECT_ID="${1:-${PROJECT_ID:-my-bigquery-test-466512}}"
REGION="${2:-${REGION:-us-central1}}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-rag-runner}"
KEY_FILE="${KEY_FILE:-gcp-key.json}"
GKE_CLUSTER_NAME="${GKE_CLUSTER_NAME:-llmops-cluster}"
AR_REPO_NAME="${AR_REPO_NAME:-llm-apps}"
GCS_BUCKET_MLFLOW="gs://${PROJECT_ID}-mlflow-artifacts"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: Project ID required. Usage: $0 [PROJECT_ID] [REGION]"
  exit 2
fi

# Prereqs
for cmd in gcloud gsutil; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: $cmd not found. Install it and retry."
    exit 3
  fi
done

# Ensure user is authenticated
ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$ACTIVE_ACCOUNT" ]; then
  echo "ERROR: No active gcloud account. Run: gcloud auth login"
  exit 4
fi
echo "Authenticated as: $ACTIVE_ACCOUNT"

echo "========================================="
echo "  GCP Setup for LLMOps Project"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Service account: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Key file: $KEY_FILE"
echo "========================================="

gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"

APIS=(
  "aiplatform.googleapis.com"
  "iam.googleapis.com"
  "cloudresourcemanager.googleapis.com"
  "storage.googleapis.com"
  "artifactregistry.googleapis.com"
  "container.googleapis.com"
  "cloudbuild.googleapis.com"
)
echo ""
echo "📡 Enabling required APIs..."
for api in "${APIS[@]}"; do
  echo "  - Enabling $api"
  gcloud services enable "$api" --project="$PROJECT_ID" || true
done

SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account if missing
echo ""
echo "👤 Checking service account..."
if ! gcloud iam service-accounts list --filter="email:${SA_EMAIL}" --format="value(email)" | grep -q .; then
  echo "  ✓ Creating service account $SA_EMAIL"
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="$SERVICE_ACCOUNT_NAME" --project="$PROJECT_ID"
else
  echo "  ✓ Service account already exists."
fi

# Grant roles (adjust least-privilege as needed)
ROLES=(
  "roles/aiplatform.user"
  "roles/artifactregistry.writer"
  "roles/storage.admin"
  "roles/container.developer"
)
echo ""
echo "🔐 Granting IAM roles to $SA_EMAIL..."
for role in "${ROLES[@]}"; do
  echo "  - Granting $role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$role" || true
done

# Create key only if not present locally and not skipped
echo ""
echo "🔑 Checking service account key..."
if [ "${SKIP_KEY:-0}" != "1" ]; then
  if [ -f "$KEY_FILE" ]; then
    echo "  ✓ Local key file $KEY_FILE already exists; skipping key creation."
    echo "  ⚠️  WARNING: DO NOT COMMIT THIS FILE TO GIT!"
  else
    echo "  ✓ Creating service account key: $KEY_FILE"
    gcloud iam service-accounts keys create "$KEY_FILE" \
      --iam-account="$SA_EMAIL" --project="$PROJECT_ID"
    echo "  ✅ Key created at $KEY_FILE"
    echo "  ⚠️  WARNING: DO NOT COMMIT THIS FILE TO GIT!"
  fi
else
  echo "  ⏭️  SKIP_KEY=1 -> skipping service account key creation."
fi

# Create GKE cluster (skip if SKIP_CLUSTER=1)
echo ""
echo "☸️  Checking GKE cluster..."
if [ "${SKIP_CLUSTER:-0}" != "1" ]; then
  if ! gcloud container clusters list --filter="name=${GKE_CLUSTER_NAME}" --format="value(name)" | grep -q .; then
    echo "  ✓ Creating GKE cluster: ${GKE_CLUSTER_NAME}"
    echo "  ⏳ This may take 5-10 minutes..."
    gcloud container clusters create "${GKE_CLUSTER_NAME}" \
      --num-nodes=3 --machine-type=n1-standard-4 --region="$REGION" --enable-ip-alias
    echo "  ✅ GKE cluster created successfully!"
  else
    echo "  ✓ GKE cluster ${GKE_CLUSTER_NAME} already exists; skipping creation."
  fi
else
  echo "  ⏭️  SKIP_CLUSTER=1 -> skipping GKE cluster creation."
fi

# Create Artifact Registry repo if not skipped
echo ""
echo "📦 Checking Artifact Registry..."
if [ "${SKIP_AR:-0}" != "1" ]; then
  if ! gcloud artifacts repositories describe "$AR_REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
    echo "  ✓ Creating Artifact Registry repo: ${AR_REPO_NAME}"
    gcloud artifacts repositories create "$AR_REPO_NAME" \
      --repository-format=docker --location="$REGION" --description="Docker repo for LLM apps"
    echo "  ✅ Artifact Registry created successfully!"
  else
    echo "  ✓ Artifact Registry repo ${AR_REPO_NAME} already exists; skipping."
  fi
else
  echo "  ⏭️  SKIP_AR=1 -> skipping Artifact Registry creation."
fi

# Create GCS bucket if not skipped
echo ""
echo "🪣 Checking GCS bucket..."
if [ "${SKIP_BUCKET:-0}" != "1" ]; then
  if ! gsutil ls -b "$GCS_BUCKET_MLFLOW" >/dev/null 2>&1; then
    echo "  ✓ Creating GCS bucket: ${GCS_BUCKET_MLFLOW}"
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "$GCS_BUCKET_MLFLOW"
    echo "  ✅ GCS bucket created successfully!"
  else
    echo "  ✓ GCS bucket ${GCS_BUCKET_MLFLOW} already exists; skipping."
  fi
else
  echo "  ⏭️  SKIP_BUCKET=1 -> skipping GCS bucket creation."
fi

echo ""
echo "========================================="
echo "  ✅ GCP Setup Complete!"
echo "========================================="
echo "Project ID: ${PROJECT_ID}"
echo "GKE Cluster: ${GKE_CLUSTER_NAME}"
echo "Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO_NAME}"
echo "MLflow GCS Bucket: ${GCS_BUCKET_MLFLOW}"
echo "Service account: ${SA_EMAIL}"
echo "Key file: ${KEY_FILE}"
echo ""
echo "⚠️  IMPORTANT: DO NOT COMMIT ${KEY_FILE} TO GIT!"
echo "========================================="