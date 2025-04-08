import uvicorn
import os
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.base import Base, engine, get_db
from app.db.init_db import init_db
from app.core.config import settings
from app.api.v1.api import api_router
import app.models as models

# Create tables
Base.metadata.create_all(bind=engine)

# Path to the frontend directory
# In Docker, frontend files are in /app/frontend
# In development, they are in the project root's frontend directory
FRONTEND_DIR = Path("/app/frontend")
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Initialize FastAPI app
app = FastAPI(
    title="SummarEase API",
    description="Text summarization API powered by AI",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router with prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    init_db(db)

# Mount the frontend static files directory
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Serve the HTML files
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/register.html", response_class=HTMLResponse)
async def serve_register():
    return FileResponse(FRONTEND_DIR / "register.html")

@app.get("/dashboard.html", response_class=HTMLResponse)
async def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/history.html", response_class=HTMLResponse)
async def serve_history():
    return FileResponse(FRONTEND_DIR / "history.html")

@app.get("/api-docs.html", response_class=HTMLResponse)
async def serve_api_docs():
    return FileResponse(FRONTEND_DIR / "api-docs.html")

# Add additional paths without .html extension for cleaner URLs
@app.get("/register", response_class=HTMLResponse)
async def serve_register_clean():
    return FileResponse(FRONTEND_DIR / "register.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard_clean():
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/history", response_class=HTMLResponse)
async def serve_history_clean():
    return FileResponse(FRONTEND_DIR / "history.html")

@app.get("/api-docs", response_class=HTMLResponse)
async def serve_api_docs_clean():
    return FileResponse(FRONTEND_DIR / "api-docs.html")

# Add direct route for Google OAuth callback
@app.get("/auth/google/callback")
async def redirect_google_callback(request: Request):
    # Construct the redirect URL to the API endpoint
    redirect_path = f"/api/v1/auth/google/callback?{request.url.query}"
    
    # Use a 302 redirect for better browser compatibility
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_path, status_code=302)

# Serve CSS file
@app.get("/styles.css")
async def serve_css():
    return FileResponse(FRONTEND_DIR / "styles.css")

# Serve script.js
@app.get("/script.js")
async def serve_script():
    return FileResponse(FRONTEND_DIR / "script.js")

if __name__ == "__main__":
    print(f"Frontend directory: {FRONTEND_DIR}")
    print(f"Frontend exists: {FRONTEND_DIR.exists()}")
    print(f"API path prefix: {settings.API_V1_STR}")
    uvicorn.run("integrated_app:app", host="0.0.0.0", port=8000, reload=True)