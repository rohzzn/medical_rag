#!/bin/bash
set -e

echo "Script will wait for Neo4j to be available before loading the dump..."

# Wait for Neo4j to be available
while true; do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 | grep -q "200"; then
    break
  fi
  echo "Waiting for Neo4j to start..."
  sleep 5
done

echo "Neo4j is up. Loading dump file..."

# Check if neo4j database is empty
NODE_COUNT=$(cypher-shell -u neo4j -p password26 "MATCH (n) RETURN count(n) as count" --format plain)
NODE_COUNT=${NODE_COUNT//[!0-9]/}

if [ "$NODE_COUNT" == "0" ]; then
  echo "Database is empty. Loading dump file..."
  
  # Stop Neo4j for dump loading
  neo4j stop
  
  # Load the dump file
  neo4j-admin database load --from-path=/import neo4j
  
  # Start Neo4j again
  neo4j start
  
  echo "Neo4j dump loaded successfully."
else
  echo "Database already has data. Skipping dump loading."
fi

# Keep the container running
tail -f /dev/null 