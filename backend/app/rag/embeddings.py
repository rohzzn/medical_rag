import os
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from app.core.config import settings

def get_embedder():
    """
    Create and return an embeddings model instance.
    """
    # Set the OPENAI_API_KEY environment variable
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    
    # Create the embedder
    embedder = OpenAIEmbeddings()
    return embedder