pipeline {
    agent any
    environment {
        // Replace with your GCP region and project ID
        PROJECT_ID = 'your-gcp-project-id'
        REGION = 'us-central1'
        IMAGE_NAME = "${REGION}-docker.pkg.dev/${PROJECT_ID}/llm-apps/advanced-rag"
        GCP_CREDENTIALS_ID = 'gcp-service-account-key' // ID of your GCP credentials in Jenkins
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/your-username/llmops-advanced-rag.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    withCredentials([file(credentialsId: GCP_CREDENTIALS_ID, variable: 'GCLOUD_KEY_FILE')]) {
                        sh 'gcloud auth activate-service-account --key-file=${GCLOUD_KEY_FILE}'
                        sh 'gcloud auth configure-docker ${REGION}-docker.pkg.dev'
                        sh "docker build -t ${IMAGE_NAME}:${env.BUILD_ID} -f app/Dockerfile ./app"
                    }
                }
            }
        }
        stage('Push Docker Image') {
            steps {
                sh "docker push ${IMAGE_NAME}:${env.BUILD_ID}"
            }
        }
        stage('Trigger Kubeflow Pipeline') {
            steps {
                // This step would typically involve a POST request to the Kubeflow Pipelines API
                // to start a new run with the image tag from this build.
                echo "Placeholder: Triggering Kubeflow pipeline with image tag: ${IMAGE_NAME}:${env.BUILD_ID}"
                // Example:
                // sh "curl -X POST -H 'Content-Type: application/json' ..."
            }
        }
    }
}