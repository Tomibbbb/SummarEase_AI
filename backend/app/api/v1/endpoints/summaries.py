from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel

from app import models
from app.api import deps
from app.core.config import settings
from app.db.base import get_db
from app.schemas.summary import Summary, SummaryCreate, SummaryList
from app.services.cohere_service import CohereService
from app.services.s3_service import S3Service
from celery_worker import process_summary

router = APIRouter()

class CohereRequest(BaseModel):
    user_id: int
    text: str

@router.post("/summarize")
def create_cohere_summary(
    *,
    request: CohereRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """Create a summary using the Cohere API."""
    if current_user["id"] != request.user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create summary for this user"
        )
    
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.credits <= 0:
        raise HTTPException(status_code=400, detail="Not enough credits to create a summary")
    
    from sqlalchemy.sql import text
    db.execute(
        text("UPDATE users SET credits = credits - 1 WHERE id = :user_id"),
        {"user_id": request.user_id}
    )
    db.commit()
    
    summary = models.Summary(
        user_id=request.user_id,
        original_text=request.text,
        status="processing",
        model_used=CohereService.DEFAULT_MODEL,
        processing_started_at=datetime.utcnow()
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    
    result = CohereService.get_summary(
        text=request.text,
        model_id=CohereService.DEFAULT_MODEL
    )
    
    if not result.get("success"):
        summary.status = "failed"
        summary.error_message = result.get("error", "Unknown error")
        db.commit()
        return {"success": False, "error": result.get("error", "Unknown error")}
    
    summary_text = result.get("summary", "")
    summary.summary_text = summary_text
    summary.status = "completed"
    summary.completed_at = datetime.utcnow()
    
    if "stats" in result:
        stats = result["stats"]
        summary.processing_time_ms = stats.get("processing_time_ms")
        summary.original_tokens = stats.get("input_tokens")
        summary.summary_tokens = stats.get("output_tokens")
        
        cost_per_1k_tokens = 0.0004
        total_tokens = (summary.original_tokens or 0) + (summary.summary_tokens or 0)
        summary.processing_cost = (total_tokens / 1000) * cost_per_1k_tokens
    
    db.commit()
    
    return {
        "success": True,
        "summary": summary_text,
        "summary_id": summary.id,
        "stats": {
            "processing_time_ms": summary.processing_time_ms,
            "input_tokens": summary.original_tokens,
            "output_tokens": summary.summary_tokens
        }
    }


@router.post("/", response_model=Summary)
def create_summary(
    *,
    db: Session = Depends(get_db),
    summary_in: SummaryCreate,
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new summary.
    
    Takes text input and model parameters, processes it asynchronously,
    and returns a summary object with status "pending".
    """
    # Check if user has enough credits
    if current_user["credits"] <= 0:
        raise HTTPException(
            status_code=400,
            detail="Not enough credits to create a summary.",
        )
    
    if summary_in.model_id not in CohereService.MODELS:
        valid_models = ", ".join(CohereService.MODELS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model ID. Choose from: {valid_models}"
        )
    
    # Deduct credits from user (using raw SQL for compatibility)
    from sqlalchemy.sql import text
    db.execute(
        text("UPDATE users SET credits = credits - 1 WHERE id = :user_id"),
        {"user_id": current_user["id"]}
    )
    db.commit()
    
    # Create summary
    summary = models.Summary(
        user_id=current_user["id"],
        original_text=summary_in.original_text,
        status="pending",
        model_used=summary_in.model_id,
        max_length=summary_in.max_length,
        min_length=summary_in.min_length,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    
    # During development: for testing without Celery, process synchronously
    try:
        # For development/testing without Celery
        process_directly = settings.PROCESS_DIRECTLY or not settings.REDIS_URL
        if process_directly:
            # Process directly (synchronously) - only for testing/development
            
            # Update status
            summary.status = "processing"
            summary.processing_started_at = datetime.utcnow()
            db.commit()
            
            # Call Cohere API
            result = CohereService.get_summary(
                text=summary.original_text,
                model_id=summary.model_used,
                max_length=summary.max_length,
                min_length=summary.min_length
            )
            
            # Update summary
            if not result.get("success"):
                summary.status = "failed"
                summary.error_message = result.get("error", "Unknown error")
            else:
                summary.summary_text = result.get("summary", "")
                summary.status = "completed"
                summary.completed_at = datetime.utcnow()
                
                # Add mock indicator if this is a mock response
                if result.get("mock", False):
                    summary.summary_text = "[MOCK MODE] " + summary.summary_text
                
                # Update statistics if available
                if "stats" in result:
                    stats = result["stats"]
                    summary.processing_time_ms = stats.get("processing_time_ms")
                    summary.original_tokens = stats.get("input_tokens")
                    summary.summary_tokens = stats.get("output_tokens")
            
            db.commit()
        else:
            # Normal async processing with Celery
            process_summary.delay(summary.id)
    except Exception as e:
        # Fall back to async processing
        print(f"Error in direct processing: {e}")
        process_summary.delay(summary.id)
    
    return summary


@router.get("/", response_model=List[Summary])
def read_summaries(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(20, ge=1, le=100, description="Limit records"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field (created_at, status)"),
    sort_desc: bool = Query(True, description="Sort descending"),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve a list of summaries for the current user.
    
    Can be filtered by status and sorted by different fields.
    """
    # Build query
    query = db.query(models.Summary).filter(models.Summary.user_id == current_user["id"])
    
    # Apply status filter if provided
    if status:
        query = query.filter(models.Summary.status == status)
    
    # Apply sorting
    if sort_by not in ["created_at", "status", "processing_time_ms"]:
        sort_by = "created_at"
        
    if sort_desc:
        query = query.order_by(desc(getattr(models.Summary, sort_by)))
    else:
        query = query.order_by(getattr(models.Summary, sort_by))
    
    # Apply pagination
    summaries = query.offset(skip).limit(limit).all()
    
    return summaries


@router.get("/count", response_model=Dict[str, Any])
def get_summary_counts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get counts of summaries by status for the current user.
    """
    # Get total counts
    counts = db.query(
        models.Summary.status,
        func.count(models.Summary.id).label("count")
    ).filter(
        models.Summary.user_id == current_user["id"]
    ).group_by(
        models.Summary.status
    ).all()
    
    # Convert to dict
    result = {
        "total": 0,
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0
    }
    
    for status, count in counts:
        result[status] = count
        result["total"] += count
    
    return result


@router.get("/models", response_model=Dict[str, Any])
def get_available_models() -> Any:
    """
    Get a list of available summarization models.
    """
    return {
        "models": CohereService.get_available_models()
    }


@router.get("/{summary_id}", response_model=Summary)
def read_summary(
    *,
    db: Session = Depends(get_db),
    summary_id: int = Path(..., description="The ID of the summary to get"),
    current_user: dict = Depends(deps.get_current_active_user),
    use_s3: bool = Query(True, description="Whether to fetch from S3 if available")
) -> Any:
    """
    Get a summary by ID.
    
    Returns the full summary object including the original text,
    summarized text, and processing details. Can optionally fetch the 
    full content from S3 if available.
    """
    # Get summary from database
    summary = db.query(models.Summary).filter(models.Summary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Check permissions - users can only see their own summaries, admins can see all
    if summary.user_id != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # If summary has an S3 location and we want to use it, fetch from S3
    if use_s3 and summary.s3_location and summary.status == "completed":
        try:
            # Get the full summary data from S3
            s3_data = S3Service.get_summary(summary.s3_location)
            
            # If we got data from S3, update the summary object with any missing details
            if s3_data and "summary_text" in s3_data:
                if not summary.summary_text and s3_data["summary_text"]:
                    summary.summary_text = s3_data["summary_text"]
                
                # We could also update other fields if needed
        except Exception as e:
            # Log the error but continue with the database version
            print(f"Warning: Could not fetch summary from S3: {e}")
    
    return summary


@router.get("/{summary_id}/share", response_model=Dict[str, Any])
def get_summary_share_url(
    *,
    db: Session = Depends(get_db),
    summary_id: int = Path(..., description="The ID of the summary to share"),
    current_user: dict = Depends(deps.get_current_active_user),
    expires_in: int = Query(3600, description="Expiration time in seconds")
) -> Any:
    """
    Generate a shareable URL for a summary.
    
    Returns a presigned URL that can be used to access the summary JSON directly
    from S3 without authentication. The URL is valid for the specified duration.
    """
    # Get summary from database
    summary = db.query(models.Summary).filter(models.Summary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Check permissions
    if summary.user_id != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Make sure the summary is completed and has an S3 location
    if summary.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail="Only completed summaries can be shared"
        )
    
    if not summary.s3_location:
        raise HTTPException(
            status_code=400,
            detail="Summary is not available for sharing (no S3 storage)"
        )
    
    # Generate a presigned URL
    url = S3Service.generate_presigned_url(summary.s3_location, expires_in)
    
    if not url:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate sharing URL"
        )
    
    return {
        "summary_id": summary.id,
        "shared_url": url,
        "expires_in": expires_in,
        "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    }


@router.delete("/{summary_id}", status_code=204)
def delete_summary(
    *,
    db: Session = Depends(get_db),
    summary_id: int = Path(..., description="The ID of the summary to delete"),
    current_user: dict = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a summary by ID.
    
    Users can only delete their own summaries. Admins can delete any summary.
    The summary is deleted from both the database and S3 storage if available.
    """
    # Find the summary in the database
    summary = db.query(models.Summary).filter(models.Summary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Check permissions
    if summary.user_id != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # If the summary has an S3 location, delete it from S3 too
    if summary.s3_location:
        try:
            S3Service.delete_summary(summary.s3_location)
        except Exception as e:
            # Log the error but continue with database deletion
            print(f"Warning: Failed to delete from S3: {e}")
    
    # Delete the summary from the database
    db.delete(summary)
    db.commit()
    
    # Don't return anything for 204 responses
    return
