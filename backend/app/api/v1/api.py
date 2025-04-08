from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.v1.endpoints import auth, users, summaries
from app.db.base import get_db
from app.api import deps
from app import models

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User routes 
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Summary routes
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])

# Home routes directly in the API file
@api_router.get("/home", tags=["home"])
def get_home_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """
    Get statistics for the home dashboard.
    """
    # Get user summary stats
    user_stats = db.query(
        func.count(models.Summary.id).label("total"),
        func.sum(models.Summary.status == "completed").label("completed"),
        func.sum(models.Summary.status == "pending").label("pending"),
        func.sum(models.Summary.status == "processing").label("processing"),
        func.sum(models.Summary.status == "failed").label("failed"),
    ).filter(models.Summary.user_id == current_user.id).first()

    # Get recent summaries
    recent_summaries = db.query(models.Summary).filter(
        models.Summary.user_id == current_user.id
    ).order_by(models.Summary.created_at.desc()).limit(5).all()

    # Convert to response format
    result = {
        "user": {
            "email": current_user.email,
            "credits": current_user.credits,
            "role": current_user.role,
            "is_active": current_user.is_active
        },
        "summaries": {
            "total": user_stats.total or 0,
            "completed": user_stats.completed or 0,
            "pending": user_stats.pending or 0,
            "processing": user_stats.processing or 0,
            "failed": user_stats.failed or 0
        },
        "recent_summaries": [
            {
                "id": summary.id,
                "status": summary.status,
                "created_at": summary.created_at,
                "completed_at": summary.completed_at,
                "model_used": summary.model_used,
                "original_text": summary.original_text[:100] + "..." if summary.original_text and len(summary.original_text) > 100 else summary.original_text
            }
            for summary in recent_summaries
        ]
    }
    
    return result