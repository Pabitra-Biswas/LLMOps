@echo off
REM Windows Batch Script for GCP Setup
REM Usage: setup_gcp.bat

SET PROJECT_ID=my-bigquery-test-466512
SET REGION=us-central1
SET SERVICE_ACCOUNT_NAME=rag-runner
SET KEY_FILE=gcp-key.json
SET GKE_CLUSTER_NAME=llmops-cluster
SET AR_REPO_NAME=llm-apps
SET GCS_BUCKET_MLFLOW=gs://%PROJECT_ID%-mlflow-artifacts

echo =========================================
echo   GCP Setup for LLMOps Project
echo =========================================
echo Project: %PROJECT_ID%
echo Region:  %REGION%
echo Service account: %SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com
echo Key file: %KEY_FILE%
echo =========================================
echo.

REM Set project and region
echo Setting project and region...
call gcloud config set project %PROJECT_ID%
call gcloud config set compute/region %REGION%
echo Project and region configured.

REM Enable APIs
echo.
echo Enabling required APIs...
gcloud services enable aiplatform.googleapis.com --project=%PROJECT_ID%
gcloud services enable iam.googleapis.com --project=%PROJECT_ID%
gcloud services enable cloudresourcemanager.googleapis.com --project=%PROJECT_ID%
gcloud services enable storage.googleapis.com --project=%PROJECT_ID%
gcloud services enable artifactregistry.googleapis.com --project=%PROJECT_ID%
gcloud services enable container.googleapis.com --project=%PROJECT_ID%
gcloud services enable cloudbuild.googleapis.com --project=%PROJECT_ID%

REM Check if service account exists
echo.
echo Checking service account...
gcloud iam service-accounts describe %SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com >nul 2>&1
if %errorlevel% equ 0 (
    echo Service account already exists.
) else (
    echo Creating service account...
    gcloud iam service-accounts create %SERVICE_ACCOUNT_NAME% --display-name="%SERVICE_ACCOUNT_NAME%" --project=%PROJECT_ID%
)

REM Grant roles
echo.
echo Granting IAM roles...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/container.developer"

REM Check for existing key file
echo.
echo Checking service account key...
if exist %KEY_FILE% (
    echo Key file %KEY_FILE% already exists; skipping key creation.
    echo WARNING: DO NOT COMMIT THIS FILE TO GIT!
) else (
    echo Creating new service account key...
    gcloud iam service-accounts keys create %KEY_FILE% --iam-account=%SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com --project=%PROJECT_ID%
    echo Key created at %KEY_FILE%
    echo WARNING: DO NOT COMMIT THIS FILE TO GIT!
)

REM Check if GKE cluster exists
echo.
echo Checking GKE cluster...
gcloud container clusters describe %GKE_CLUSTER_NAME% --region=%REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo GKE cluster %GKE_CLUSTER_NAME% already exists; skipping creation.
) else (
    echo Creating GKE cluster: %GKE_CLUSTER_NAME%
    echo This may take 5-10 minutes...
    gcloud container clusters create %GKE_CLUSTER_NAME% --num-nodes=3 --machine-type=n1-standard-4 --region=%REGION% --enable-ip-alias
)

REM Check if Artifact Registry exists
echo.
echo Checking Artifact Registry...
gcloud artifacts repositories describe %AR_REPO_NAME% --location=%REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo Artifact Registry repo %AR_REPO_NAME% already exists; skipping.
) else (
    echo Creating Artifact Registry repo: %AR_REPO_NAME%
    gcloud artifacts repositories create %AR_REPO_NAME% --repository-format=docker --location=%REGION% --description="Docker repo for LLM apps"
)

REM Check if GCS bucket exists
echo.
echo Checking GCS bucket...
gsutil ls -b %GCS_BUCKET_MLFLOW% >nul 2>&1
if %errorlevel% equ 0 (
    echo GCS bucket %GCS_BUCKET_MLFLOW% already exists; skipping.
) else (
    echo Creating GCS bucket: %GCS_BUCKET_MLFLOW%
    gsutil mb -p %PROJECT_ID% -l %REGION% %GCS_BUCKET_MLFLOW%
)

echo.
echo =========================================
echo   GCP Setup Complete!
echo =========================================
echo Project ID: %PROJECT_ID%
echo GKE Cluster: %GKE_CLUSTER_NAME%
echo Artifact Registry: %REGION%-docker.pkg.dev/%PROJECT_ID%/%AR_REPO_NAME%
echo MLflow GCS Bucket: %GCS_BUCKET_MLFLOW%
echo Service account: %SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com
echo Key file: %KEY_FILE%
echo.
echo WARNING: DO NOT COMMIT %KEY_FILE% TO GIT!
echo =========================================
pause