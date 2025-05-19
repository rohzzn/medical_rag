import os
from neo4j_graphrag.llm import OpenAILLM
from app.core.config import settings

def get_llm():
    """
    Create and return an LLM instance exactly as in the Jupyter notebook.
    """
    # Make sure the OpenAI API key is set
    if settings.OPENAI_API_KEY:
        # Show first and last few characters of the key for debugging
        masked_key = settings.OPENAI_API_KEY[:4] + "..." + settings.OPENAI_API_KEY[-4:] if len(settings.OPENAI_API_KEY) > 8 else "****"
        print(f"Using OpenAI API key: {masked_key}")
        
        # Set the environment variable
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    elif "OPENAI_API_KEY" in os.environ:
        # Show first and last few characters of the key for debugging
        masked_key = os.environ["OPENAI_API_KEY"][:4] + "..." + os.environ["OPENAI_API_KEY"][-4:] if len(os.environ["OPENAI_API_KEY"]) > 8 else "****"
        print(f"Using OpenAI API key from environment: {masked_key}")
    else:
        raise ValueError("OPENAI_API_KEY not found in settings or environment")
    
    try:
        # Create the LLM - identical to notebook
        llm = OpenAILLM(
            model_name=settings.LLM_MODEL,
            model_params={"temperature": 0.0}
        )
        print(f"OpenAI LLM created successfully with model: {settings.LLM_MODEL}")
        return llm
    except Exception as e:
        print(f"Error creating OpenAI LLM: {e}")
        raise