#!/bin/bash
set -e

echo "*** Starting Neo4j initialization ***"

# Check for the specific .dump file
DUMP_FILE="/import/neo4j_dump/neo4j.dump"
if [ -f "$DUMP_FILE" ]; then
    echo "Found neo4j.dump file at $DUMP_FILE"
    
    # Load the dump file directly
    echo "Loading dump file..."
    neo4j-admin database load neo4j --from-path="/import/neo4j_dump" --overwrite-destination || {
        echo "Error loading dump file"
        echo "Contents of /import/neo4j_dump:"
        ls -la /import/neo4j_dump/
        echo "Dump file exists: $(test -f "$DUMP_FILE" && echo "Yes" || echo "No")"
        echo "Dump file size: $(ls -lh "$DUMP_FILE" 2>/dev/null || echo "N/A")"
    }
    
    echo "Dump loading completed."
else
    echo "WARNING: neo4j.dump file not found at $DUMP_FILE"
    echo "Contents of /import directory:"
    ls -la /import/
    echo "Starting with empty database."
fi

# Start Neo4j
echo "Starting Neo4j..."
exec neo4j console 