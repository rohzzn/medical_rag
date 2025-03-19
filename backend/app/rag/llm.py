import os
from neo4j_graphrag.llm import OpenAILLM
from app.core.config import settings

def get_llm():
    """
    Create and return an LLM instance.
    """
    # Set the OPENAI_API_KEY environment variable if it exists in settings
    if settings.OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    elif "OPENAI_API_KEY" not in os.environ:
        raise ValueError("OPENAI_API_KEY not found in environment variables or settings")
    
    # Create the LLM
    llm = OpenAILLM(
        model_name=settings.LLM_MODEL,
        model_params={"temperature": 0.0}
    )
    return llm