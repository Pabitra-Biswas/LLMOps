
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

# --- CHANGE 1: Import the necessary Hook ---
from airflow.providers.google.common.hooks.base_google import GoogleBaseHook


# The GCP connection ID you created in the Airflow UI
GCP_CONN_ID = "google_cloud_default"
# Your GCP Project ID
GCP_PROJECT_ID = "my-bigquery-test-466512"
# The region where you want to deploy the model
GCP_REGION = "us-central1"

def deploy_model_to_vertex_ai(project_id: str, region: str, gcp_conn_id: str, **context):
    """
    A Python function that uses the Vertex AI SDK to deploy a model.
    """
    from google.cloud import aiplatform

    docker_image_uri = context["dag_run"].conf.get("docker_image_uri")
    if not docker_image_uri:
        raise ValueError("'docker_image_uri' must be provided in the DAG run configuration.")

    print(f"Starting deployment for image: {docker_image_uri}")

    # --- CHANGE 2: Instantiate the Hook to get credentials ---
    # The hook manages the connection and authentication details securely.
    gcp_hook = GoogleBaseHook(gcp_conn_id=gcp_conn_id)
    credentials = gcp_hook.get_credentials()

    # 1. Initialize the Vertex AI client, passing in the credentials from the hook
    aiplatform.init(
        project=project_id,
        location=region,
        credentials=credentials
    )

    model_display_name = "advanced-rag-agent-airflow"
    endpoint_display_name = f"{model_display_name}-endpoint"

    # 2. Upload the model
    print(f"Uploading model '{model_display_name}'...")
    model = aiplatform.Model.upload(
        display_name=model_display_name,
        serving_container_image_uri=docker_image_uri,
        serving_container_predict_route="/predict",
        serving_container_health_route="/health",
        serving_container_ports=[8080],
    )
    print(f"Model uploaded successfully: {model.resource_name}")

    # 3. Create a new endpoint
    print(f"Creating endpoint '{endpoint_display_name}'...")
    endpoint = aiplatform.Endpoint.create(display_name=endpoint_display_name)
    print(f"Endpoint created successfully: {endpoint.resource_name}")

    # 4. Deploy the model to the endpoint
    print("Deploying model to endpoint...")
    # The service account that has permission to call the Gemini API
    DEPLOYMENT_SERVICE_ACCOUNT = "rag-runner@my-bigquery-test-466512.iam.gserviceaccount.com"

    endpoint.deploy(
        model=model,
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=1,
        traffic_split={"0": 100},
        sync=True,
        # Tell the endpoint to run the model container using this specific identity
        service_account=DEPLOYMENT_SERVICE_ACCOUNT
    )
    print("Model deployed successfully!")


with DAG(
    dag_id="vertex_ai_rag_model_deployment",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["mlops", "rag", "vertex-ai"],
) as dag:
    deploy_task = PythonOperator(
        task_id="deploy_rag_model_to_vertex",
        python_callable=deploy_model_to_vertex_ai,
        # --- CHANGE 3: Pass gcp_conn_id via op_kwargs instead ---
        # We pass the connection ID as a regular argument to our Python function.
        op_kwargs={
            "project_id": GCP_PROJECT_ID,
            "region": GCP_REGION,
            "gcp_conn_id": GCP_CONN_ID
        },
    )