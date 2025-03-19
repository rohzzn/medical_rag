import os
from neo4j_graphrag.llm import OpenAILLM
from app.core.config import settings

def get_llm():
    """
    Create and return an LLM instance.
    """
    # Set the OPENAI_API_KEY environment variable
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    
    # Create the LLM
    llm = OpenAILLM(
        model_name=settings.LLM_MODEL,
        model_params={"temperature": 0.0}
    )
    return llm