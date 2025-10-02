import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import component
from kfp.v2.compiler import Compiler
import os

# --- Component: Deploy to Vertex AI ---
# This component takes a Docker image and deploys it as a Vertex AI Endpoint.
@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform==1.36.1"],
)
def deploy_rag_model_to_vertex(
    project: str,
    location: str,
    serving_image_uri: str,
    model_display_name: str,
    endpoint_display_name: str,
):
    """
    Deploys a containerized model to a new Vertex AI Endpoint.
    """
    from google.cloud import aiplatform

    aiplatform.init(project=project, location=location)

    # Upload the model to Vertex AI Model Registry
    model = aiplatform.Model.upload(
        display_name=model_display_name,
        serving_container_image_uri=serving_image_uri,
        serving_container_predict_route="/predict",
        serving_container_health_route="/health",
        serving_container_ports=[8080],
    )
    print(f"Model {model.resource_name} uploaded.")

    # Create an endpoint and deploy the model
    endpoint = aiplatform.Endpoint.create(display_name=endpoint_display_name)
    endpoint.deploy(
        model=model,
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=2,
        traffic_split={"0": 100},
        sync=True,
    )
    print(f"Model deployed to endpoint {endpoint.resource_name}.")

# --- Kubeflow Pipeline Definition ---
@dsl.pipeline(
    name="llm-advanced-rag-deployment-pipeline",
    description="A pipeline to deploy the advanced RAG model to Vertex AI."
)
def rag_deployment_pipeline(
    project_id: str,
    region: str,
    docker_image_uri: str,
    model_name: str = "advanced-rag-agent",
    endpoint_name: str = "advanced-rag-endpoint",
):
    deploy_task = deploy_rag_model_to_vertex(
        project=project_id,
        location=region,
        serving_image_uri=docker_image_uri,
        model_display_name=model_name,
        endpoint_display_name=endpoint_name,
    )

# --- Compiler ---
# This script can be run to compile the pipeline into a JSON file.
if __name__ == "__main__":
    Compiler().compile(
        pipeline_func=rag_deployment_pipeline,
        package_path="rag_deployment_pipeline.json",
    )
    print("Pipeline compiled successfully to rag_deployment_pipeline.json")