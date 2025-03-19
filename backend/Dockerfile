FROM python:3.9-slim

WORKDIR /app/

# Install utilities for debugging
RUN apt-get update && apt-get install -y curl iputils-ping netcat procps

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a startup script for better debugging
RUN echo '#!/bin/bash\n\
echo "Current working directory: $(pwd)"\n\
echo "Directory contents:"\n\
ls -la\n\
echo "Environment variables:"\n\
env | grep -E "NEO4J|OPENAI|POSTGRES"\n\
echo "Testing Neo4j connection:"\n\
nc -zv neo4j 7687 || echo "Cannot connect to Neo4j"\n\
echo "Starting application..."\n\
python -m app.env_setup\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Run the application
CMD ["/app/start.sh"]