import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables directly before other imports
from app.env_setup import setup_env
setup_env()

# Now import the rest of the modules
from app.api import auth, users, queries
from app.core.config import settings
from app.db.models import Base

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
    print(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)