# Medical RAG System

## Troubleshooting

### Summary of Fixes
We've addressed two main issues in the system:

1. **Neo4j Connection Issues**: Fixed by ensuring Neo4j listens on all interfaces (0.0.0.0) instead of just localhost
2. **APOC Plugin Issues**: Fixed by replacing the `apoc.text.join` function with Cypher's built-in `reduce()` function

The system should now be able to successfully connect to Neo4j and execute queries without requiring the APOC plugin.

### Neo4j Connection Issues
If you encounter connection issues between the backend and Neo4j, it might be because Neo4j is configured to only listen on localhost by default. The solution is to use a custom Neo4j configuration that sets the listening address to 0.0.0.0.

This is already implemented in the project by:
1. Creating a custom configuration file at `scripts/neo4j.conf` with the following settings:
   ```
   server.default_listen_address=0.0.0.0
   server.bolt.listen_address=0.0.0.0:7687
   server.http.listen_address=0.0.0.0:7474
   ```
2. Copying this configuration into the Neo4j container in `Dockerfile.neo4j`

You can verify the connection by checking the Neo4j logs to confirm it's listening on all interfaces:
```
docker logs medical_rag-neo4j-1 | grep Bolt
```

The logs should show: `Bolt enabled on 0.0.0.0:7687` instead of `Bolt enabled on localhost:7687`.

### APOC Plugin Issues
If you encounter errors like `Unknown function 'apoc.text.join'`, it's because the APOC plugin isn't properly loaded in Neo4j. Rather than troubleshooting the plugin installation, we've modified the Cypher queries to use built-in functions:

1. Instead of using `apoc.text.join([list], delimiter)`, we use Cypher's `reduce()` function:
   ```cypher
   // Before:
   substring(apoc.text.join([c in chunks | c.text], '\n---\n'), 0, 10000000) AS truncated_chunk_texts
   
   // After:
   reduce(s = '', t IN chunk_texts | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + t) AS truncated_chunk_texts
   ```

2. This change is implemented in `backend/app/rag/retrievers.py` in the `retrieval_query` string.

The `reduce()` function in Cypher is a powerful alternative that accumulates a value by applying an expression to each item in a list. 