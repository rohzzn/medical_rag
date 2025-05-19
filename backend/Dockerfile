# Create a new file: backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app/

# Install system dependencies (modified to use netcat-openbsd)
RUN apt-get update && \
    apt-get install -y curl iputils-ping netcat-openbsd procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD python -m app.env_setup && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload