from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.api import auth, users, queries
from app.core.config import settings
from app.db.models import Base

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
try:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {e}")

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(queries.router, prefix=f"{settings.API_V1_STR}/queries", tags=["queries"])


@app.get("/")
def root():
    return {"message": "Welcome to the Medical RAG API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)