from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# This import now points to the file with the modern dspy v3.x code
from dspy_agent import load_rag_agent

app = FastAPI(
    title="Advanced RAG API with DSPy v3",
    description="An API serving a compiled RAG agent built with the latest DSPy.",
    version="1.0.0"
)

# --- Load Agent on Startup ---
# The agent is created and compiled when the server starts.
# This ensures the optimized agent is ready to serve requests.
try:
    rag_agent = load_rag_agent()
except Exception as e:
    rag_agent = None
    print(f"FATAL: Error loading/compiling DSPy agent on startup: {e}")
    # In a real app, you might want the server to fail to start if the agent doesn't load.

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

@app.on_event("startup")
async def startup_event():
    if not rag_agent:
        raise RuntimeError("DSPy agent could not be loaded. Check server logs for errors.")

@app.get("/health")
def read_health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/predict", response_model=QueryResponse)
async def predict(request: QueryRequest):
    """
    Receives a question and returns the answer from the compiled RAG agent.
    """
    try:
        prediction = rag_agent(question=request.question)
        return QueryResponse(answer=prediction.answer)
    except Exception as e:
        # Log the full error for debugging
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during prediction.")
