import os
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from app.core.config import settings

def get_embedder():
    """
    Create and return an embeddings model instance.
    """
    # First try to get from environment directly
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If not found in environment, try settings
    if not api_key and hasattr(settings, "OPENAI_API_KEY"):
        print(f"Getting API key from settings: {settings.OPENAI_API_KEY[:5]}...")
        api_key = settings.OPENAI_API_KEY
    
    # If we have an API key, set it in environment
    if api_key:
        print(f"OpenAI API key found (starts with: {api_key[:4]}...)")
        os.environ["OPENAI_API_KEY"] = api_key
    else:
        print("WARNING: No OpenAI API key found in environment or settings")
        raise ValueError("OPENAI_API_KEY not found in environment variables or settings")
    
    # Create the embedder
    embedder = OpenAIEmbeddings()
    return embedder