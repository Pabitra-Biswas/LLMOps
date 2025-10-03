FROM python:3.10-slim
WORKDIR /app

# Copy just the requirements first for better layer caching
COPY web-proxy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend proxy code AND the frontend code into the image
COPY ./web-proxy/ .
COPY ./frontend/ ./frontend/

# CORRECTED CMD: Use the shell form to evaluate the $PORT variable
CMD uvicorn main:app --host 0.0.0.0 --port $PORT