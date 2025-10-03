
# web-proxy/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.cloud import aiplatform

# --- Configuration ---
# These will be set by Cloud Run's environment
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "my-bigquery-test-466512")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
ENDPOINT_ID = os.getenv("ENDPOINT_ID", "1694684968472543232")

app = FastAPI()

# --- Pydantic Models ---
class Question(BaseModel):
    question: str

# --- API Endpoints ---
@app.get("/")
async def get_index():
    """Serves the frontend index.html file."""
    return FileResponse("frontend/index.html")

@app.post("/ask")
async def ask_question(request: Question):
    """Receives a question from the frontend, calls Vertex AI, and returns the answer."""
    try:
        aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
        endpoint = aiplatform.Endpoint(endpoint_name=ENDPOINT_ID)

        # The format Vertex AI expects for its instances
        instances = [{"question": request.question}]
        
        response = endpoint.predict(instances=instances)
        
        # Extract the answer from the prediction response
        answer = response.predictions[0]['answer']
        return {"answer": answer}
        
    except Exception as e:
    # Print the full, detailed error to the Cloud Run logs for debugging
        print(f"ERROR calling Vertex AI endpoint: {e}") 
        # Forward a more useful error message to the user
        raise HTTPException(status_code=500, detail=f"Error from backend model: {e}")