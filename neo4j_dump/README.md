# Neo4j Dump Import Instructions

This directory is used to store your Neo4j dump files for importing into the Neo4j database.

## Steps to use the Neo4j dump:

1. Place your Neo4j dump file(s) in this directory (`neo4j_dump/`).
2. Make sure you have Docker and Docker Compose installed.
3. Run the `loaddash.sh` script from the project root:

```bash
./loaddash.sh
```

The script will:
- Stop any running containers
- Remove Neo4j volumes to ensure a clean import
- Start containers with a clean configuration
- Load the dump file directly into the Neo4j container
- Configure the password

## After Import

Once the script completes successfully, you can access:
- Neo4j browser at http://localhost:7474
  - Username: neo4j
  - Password: password26

## Troubleshooting

If the container name in the script doesn't match your environment, modify the `docker exec` line in the `loaddash.sh` script to match the actual container name. You can check the container name with:

```bash
docker ps
``` 