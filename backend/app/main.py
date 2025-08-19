import os
from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.orm import Session

# Load environment variables directly before other imports
from app.env_setup import setup_env
setup_env()

# Now import the rest of the modules
from app.api import auth, users, queries, rag_endpoint, ui_rag_endpoint
from app.core.config import settings
from app.db.models import Base
from app.db import models, crud
from app.db.session import engine, get_db
from app.core import security
from app.schemas.user import User
from app.check_env import check_required_env_vars

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check required environment variables
check_required_env_vars()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# Create database tables
try:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except SQLAlchemyError as e:
    print(f"Error creating database tables: {e}")
except Exception as e:
    print(f"Unexpected error creating database tables: {e}")

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(queries.router, prefix=f"{settings.API_V1_STR}/queries", tags=["queries"])
app.include_router(rag_endpoint.router, prefix=f"{settings.API_V1_STR}/rag", tags=["rag"])
app.include_router(ui_rag_endpoint.router, prefix=f"{settings.API_V1_STR}/ui-rag", tags=["ui-rag"])

# Retriever type endpoint - new!
@app.get("/api/v1/retriever-type")
async def get_retriever_type():
    retriever_type = os.getenv("RETRIEVER_TYPE", "hybrid")
    return {"retriever_type": retriever_type}

@app.post("/api/v1/retriever-type")
async def set_retriever_type(retriever_type: str = Header(...)):
    if retriever_type not in ["hybrid", "vector_cypher", "vector"]:
        raise HTTPException(status_code=400, detail="Invalid retriever type")
    
    # In production, this would update environment variables or a database setting
    # For now, we'll just return the new value
    os.environ["RETRIEVER_TYPE"] = retriever_type  # Actually set it in the environment
    return {"retriever_type": retriever_type, "status": "updated"}

@app.get("/")
def root():
    return {"message": "Welcome to the Medical RAG API"}

@app.get("/health")
def health_check():
    """Health check endpoint for the API"""
    return {
        "status": "ok",
        "openai_key_available": bool(os.environ.get("OPENAI_API_KEY")),
        "database_uri": settings.SQLALCHEMY_DATABASE_URI is not None,
        "neo4j_uri": settings.NEO4J_URI is not None
    }

@app.get("/api/v1/me", response_model=User)
def read_users_me(current_user: User = Depends(auth.get_current_user)):
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)