#!/bin/bash

# --- Configuration ---
IMAGE_NAME="advanced-rag-local"
TAG="latest"
CONTAINER_NAME="my-rag-app" # <-- A consistent name for your container
GCP_KEY_FILE="gcp-key.json"  # <-- The name of your service account key file

# --- Pre-run Check ---
# Make sure the GCP key file actually exists before we start.
if [ ! -f "$GCP_KEY_FILE" ]; then
    echo "ERROR: GCP key file not found at '$GCP_KEY_FILE'."
    echo "Please download your service account JSON key and place it in the project root."
    exit 1
fi

# --- Script ---

# Stop and remove the container if it already exists from a previous run.
echo "Cleaning up old container named '${CONTAINER_NAME}' (if it exists)..."
docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true

# Build a fresh image with your latest code.
echo "Building Docker image: ${IMAGE_NAME}:${TAG}"
docker build -t ${IMAGE_NAME}:${TAG} -f app/Dockerfile ./app
if [ $? -ne 0 ]; then
    echo "Docker build failed. Exiting."
    exit 1
fi
echo "Docker build successful."

# Run the new container with the GCP service account key mounted.
# The application will be available on http://localhost:9091
echo "Running Docker container '${CONTAINER_NAME}' on http://localhost:9091"
echo "Press [CTRL+C] in this terminal to stop the container."
docker run \
    -p 9091:8080 \
    --name ${CONTAINER_NAME} \
    -v "$(pwd)/${GCP_KEY_FILE}:/secrets/key.json:ro" \
    -e GOOGLE_APPLICATION_CREDENTIALS="/secrets/key.json" \
    -e GCP_PROJECT_ID="my-bigquery-test-466512" \
    ${IMAGE_NAME}:${TAG}