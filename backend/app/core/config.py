import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Medical RAG API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://localhost:3000"]
    
    # Security
    SECRET_KEY: str = Field(default=os.environ.get("SECRET_KEY", "supersecretkey"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Neo4j settings
    NEO4J_URI: str = Field(default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    NEO4J_USERNAME: str = Field(default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    NEO4J_PASSWORD: str = Field(default=os.environ.get("NEO4J_PASSWORD", "password"))
    
    # PostgreSQL settings
    POSTGRES_SERVER: str = Field(default=os.environ.get("POSTGRES_SERVER", "localhost"))
    POSTGRES_USER: str = Field(default=os.environ.get("POSTGRES_USER", "postgres"))
    POSTGRES_PASSWORD: str = Field(default=os.environ.get("POSTGRES_PASSWORD", "postgres"))
    POSTGRES_DB: str = Field(default=os.environ.get("POSTGRES_DB", "app"))
    SQLALCHEMY_DATABASE_URI: str = None
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(default=os.environ.get("OPENAI_API_KEY", ""))
    LLM_MODEL: str = Field(default=os.environ.get("LLM_MODEL", "gpt-4o"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construct DB URI
        self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"


settings = Settings()