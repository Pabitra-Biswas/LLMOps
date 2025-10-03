# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file from the 'app' subfolder into the container
# This is the corrected path
COPY app/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the 'app' subfolder into the container
# This is also corrected to only copy the relevant app code
COPY ./app/ .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application (this should be the Vertex AI compatible version)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]