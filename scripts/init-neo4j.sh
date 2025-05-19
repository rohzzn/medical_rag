#!/bin/bash
set -e

echo "*** Starting Neo4j initialization ***"

# Parse the NEO4J_AUTH environment variable to get username and password
IFS='/' read -r AUTH_USERNAME AUTH_PASSWORD <<< "${NEO4J_AUTH:-neo4j/password26}"
echo "Using authentication: username=$AUTH_USERNAME, password=****"

# Check for the specific .dump file
DUMP_FILE="/import/neo4j_dump/neo4j.dump"
if [ -f "$DUMP_FILE" ]; then
    echo "Found neo4j.dump file at $DUMP_FILE"
    
    # Remove any existing auth file first to ensure clean state
    rm -f /var/lib/neo4j/data/dbms/auth
    
    # Set the initial password before loading anything
    echo "Setting initial admin password..."
    neo4j-admin dbms set-initial-password "$AUTH_PASSWORD" || echo "Password may already be set"
    
    # Now load the dump file
    echo "Loading dump file..."
    neo4j-admin database load neo4j --from-path="/import/neo4j_dump" --overwrite-destination || {
        echo "Error loading dump file"
        echo "Contents of /import/neo4j_dump:"
        ls -la /import/neo4j_dump/
        echo "Dump file exists: $(test -f "$DUMP_FILE" && echo "Yes" || echo "No")"
        echo "Dump file size: $(ls -lh "$DUMP_FILE" 2>/dev/null || echo "N/A")"
    }
    
    echo "Dump loading completed."
    
    # Force the password in auth file directly as a backup method
    echo "Ensuring auth credentials are set..."
    mkdir -p /var/lib/neo4j/data/dbms
    if [ -f /var/lib/neo4j/data/dbms/auth ]; then
        rm -f /var/lib/neo4j/data/dbms/auth
    fi
    
    # Set the password again after loading the dump to be sure
    neo4j-admin dbms set-initial-password "$AUTH_PASSWORD" || echo "Could not reset password after dump"
        
else
    echo "WARNING: neo4j.dump file not found at $DUMP_FILE"
    echo "Contents of /import directory:"
    ls -la /import/
    echo "Starting with empty database."
    
    # Set password anyway
    echo "Setting password for new database..."
    neo4j-admin dbms set-initial-password "$AUTH_PASSWORD" || echo "Failed to set password"
fi

# Create auth file if it doesn't exist (fallback mechanism)
if [ ! -f /var/lib/neo4j/data/dbms/auth ]; then
    echo "Creating auth file manually..."
    mkdir -p /var/lib/neo4j/data/dbms
    # Using pre-hashed password just in case
    echo "${AUTH_USERNAME}:SHA-256,03AC674216F3E15C761EE1A5E255F067953623C8B388B4459E13F978D7C846F4:" > /var/lib/neo4j/data/dbms/auth
    chmod 600 /var/lib/neo4j/data/dbms/auth
fi

# Start Neo4j
echo "Starting Neo4j..."
exec neo4j console 