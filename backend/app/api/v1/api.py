from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, summaries

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User routes 
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Summary routes
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])