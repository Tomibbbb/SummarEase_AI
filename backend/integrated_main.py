import uvicorn
import os
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from s3_utils import s3_client, S3_BUCKET_NAME

from app.db.base import Base, engine, get_db
from app.db.init_db import init_db
from app.core.config import settings
from app.api.v1.api import api_router
import app.models as models

# Create all tables in database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SummarEase API",
    description="Text summarization API powered by AI",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Define the path to the frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Serve static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    init_db(db)

@app.get("/api")
async def api_root():
    return {
        "message": "Welcome to SummarEase API",
        "version": app.version,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "api_version": app.version
    }

@app.get("/test-s3")
async def test_s3_connection():
    """
    Test S3 connection by uploading a sample file and generating a view URL.
    
    This endpoint helps verify that your S3 configuration is working properly.
    It creates a small text file, uploads it to your S3 bucket, and returns
    a pre-signed URL that you can use to view the file.
    """
    # Make sure we have all required credentials
    if not S3_BUCKET_NAME:
        raise HTTPException(
            status_code=500, 
            detail="S3 bucket name not configured. Check your environment variables."
        )
    
    # Where we'll store our test file
    file_path = "test_upload.txt"
    s3_key = f"uploads/test-{int(time.time())}.txt"  # Add timestamp to prevent caching

    try:
        # Create a simple test file
        with open(file_path, "w") as f:
            f.write("Hello from SummarEase! S3 connection test file.")

        # Upload to S3
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        
        # Create a URL that works for the next hour
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        return {
            "status": "success",
            "message": f"File successfully uploaded to S3 bucket: {S3_BUCKET_NAME}",
            "file_key": s3_key,
            "presigned_url": url
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"S3 connection test failed: {str(e)}"
        )
    finally:
        # Always clean up the local test file
        if os.path.exists(file_path):
            os.remove(file_path)

# Route handlers for HTML pages
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/register", response_class=HTMLResponse)
async def serve_register():
    return FileResponse(FRONTEND_DIR / "register.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/history", response_class=HTMLResponse)
async def serve_history():
    return FileResponse(FRONTEND_DIR / "history.html")

@app.get("/api-docs", response_class=HTMLResponse)
async def serve_api_docs():
    return FileResponse(FRONTEND_DIR / "api-docs.html")

# Serve other static files
@app.get("/{file_path:path}")
async def serve_static_files(file_path: str):
    file = FRONTEND_DIR / file_path
    if file.exists():
        return FileResponse(file)
    else:
        return FileResponse(FRONTEND_DIR / "index.html")

if __name__ == "__main__":
    uvicorn.run("integrated_main:app", host="0.0.0.0", port=8000, reload=True)