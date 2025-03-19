import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Medical RAG API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Neo4j settings
    NEO4J_URI: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.environ.get("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.environ.get("NEO4J_PASSWORD", "password")
    
    # PostgreSQL settings
    POSTGRES_SERVER: str = os.environ.get("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "app")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o")
    
    # Database URI (will be set in model_post_init)
    SQLALCHEMY_DATABASE_URI: str = ""
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"  # This allows extra fields that aren't explicitly defined
    }
    
    def model_post_init(self, __context):
        # Set the database URI after initialization
        self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"


settings = Settings()