#!/bin/bash

echo "Stopping any running containers..."
docker-compose down

echo "Removing Neo4j volumes..."
docker volume rm medical_rag_neo4j-data medical_rag_neo4j-logs medical_rag_neo4j-plugins || true

echo "Starting containers with clean configuration..."
docker-compose up -d neo4j

echo "Waiting for Neo4j to start up..."
sleep 20

echo "Loading the dump file directly into the running container..."
docker exec -it medical_rag-neo4j-1 bash -c '
  echo "Loading dump file..."
  neo4j stop
  sleep 5
  ls -la /import/neo4j_dump
  neo4j-admin database load neo4j --from-path=/import/neo4j_dump --overwrite-destination=true
  echo "Starting Neo4j..."
  neo4j start
  sleep 5
  echo "Creating necessary indexes..."
  echo "Dump loaded successfully!"
'

echo "Creating vector indexes..."
sleep 5
docker exec -it medical_rag-neo4j-1 cypher-shell -u neo4j -p password26 'CREATE VECTOR INDEX text_embeddings IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: "cosine"}};'
docker exec -it medical_rag-neo4j-1 cypher-shell -u neo4j -p password26 'CREATE FULLTEXT INDEX text_embeddings2 IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text];'

echo "Starting remaining containers..."
docker-compose up -d

echo "Setup complete! You should now be able to access:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- Neo4j browser: http://localhost:7474"
echo "  Username: neo4j"
echo "  Password: password26" 