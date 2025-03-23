import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.base import Base, engine, get_db
from app.db.init_db import init_db
from app.core.config import settings
import app.models as models

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SummarEase API",
    description="Text summarization API powered by AI",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    init_db(db)

@app.get("/")
async def root():
    return {
        "message": "Welcome to SummarEase API",
        "version": app.version,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify database connection and API availability.
    Important for container health probes in orchestrated environments.
    """
    # Check database connection
    try:
        # Execute a simple query to check DB connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "api_version": app.version
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)