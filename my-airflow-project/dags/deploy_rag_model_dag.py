from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

# The GCP connection ID you created in the Airflow UI
GCP_CONN_ID = "google_cloud_default"
# Your GCP Project ID
GCP_PROJECT_ID = "my-bigquery-test-466512"
# The region where you want to deploy the model
GCP_REGION = "us-central1" # Or "us-east1", etc.

def deploy_model_to_vertex_ai(project_id: str, region: str, **context):
    """
    A Python function that uses the Vertex AI SDK to deploy a model.
    This is the core logic of our deployment task.
    """
    from google.cloud import aiplatform

    # Retrieve the Docker image URI passed from the trigger command
    docker_image_uri = context["dag_run"].conf.get("docker_image_uri")
    if not docker_image_uri:
        raise ValueError("'docker_image_uri' must be provided in the DAG run configuration.")

    print(f"Starting deployment for image: {docker_image_uri}")

    # 1. Initialize the Vertex AI client
    aiplatform.init(project=project_id, location=region)

    model_display_name = "advanced-rag-agent-airflow"
    endpoint_display_name = f"{model_display_name}-endpoint"

    # 2. Upload the model to Vertex AI Model Registry
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
    endpoint.deploy(
        model=model,
        machine_type="n1-standard-4", # You can choose your machine type here
        min_replica_count=1,
        max_replica_count=1,
        traffic_split={"0": 100},
        sync=True, # Waits for the deployment to complete
    )
    print("Model deployed successfully!")


with DAG(
    dag_id="vertex_ai_rag_model_deployment",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None, # This DAG is meant to be triggered manually
    tags=["mlops", "rag", "vertex-ai"],
) as dag:
    deploy_task = PythonOperator(
        task_id="deploy_rag_model_to_vertex",
        python_callable=deploy_model_to_vertex_ai,
        op_kwargs={"project_id": GCP_PROJECT_ID, "region": GCP_REGION},
        # Ensure this task uses the GCP connection you configured
        gcp_conn_id=GCP_CONN_ID,
    )