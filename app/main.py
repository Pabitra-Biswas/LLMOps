# app/main.py (Corrected for Vertex AI Compatibility)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel # Corrected from pydantic
from typing import List, Any

# Import your DSPy agent logic
from dspy_agent import load_rag_agent

app = FastAPI(
    title="Vertex AI Compatible RAG Model",
    version="2.0.0"
)

# --- Load Agent on Startup ---
rag_agent = load_rag_agent()

# --- Pydantic Models for Vertex AI Compatibility ---

class PredictionInstance(BaseModel):
    question: str

class VertexRequest(BaseModel):
    instances: List[PredictionInstance]

class VertexResponse(BaseModel):
    predictions: List[Any]

# --- API Endpoints ---

# Health check endpoint is required by Vertex AI for deployment
@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}

# Prediction endpoint now uses the Vertex AI schema
@app.post("/predict", response_model=VertexResponse)
async def predict(request: VertexRequest):
    predictions = []
    try:
        for instance in request.instances:
            agent_prediction = rag_agent(question=instance.question)
            # The prediction for each instance can be a simple dict
            predictions.append({"answer": agent_prediction.answer})
        
        # The final response must be wrapped in a 'predictions' key
        return VertexResponse(predictions=predictions)
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during prediction.")
