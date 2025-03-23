from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.core.config import settings
from app.db.base import get_db
from app.schemas.summary import Summary, SummaryCreate
from celery_worker import process_summary

router = APIRouter()


@router.post("/", response_model=Summary)
def create_summary(
    *,
    db: Session = Depends(get_db),
    summary_in: SummaryCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Create new summary."""
    # Check if user has enough credits
    if current_user.credits <= 0:
        raise HTTPException(
            status_code=400,
            detail="Not enough credits to create a summary.",
        )
    
    # Deduct credits
    current_user.credits -= 1
    db.add(current_user)
    
    # Create summary
    summary = models.Summary(
        user_id=current_user.id,
        original_text=summary_in.original_text,
        status="pending",
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    
    # Submit task to Celery queue
    process_summary.delay(summary.id)
    
    return summary


@router.get("/", response_model=List[Summary])
def read_summaries(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Retrieve summaries."""
    summaries = (
        db.query(models.Summary)
        .filter(models.Summary.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return summaries


@router.get("/{summary_id}", response_model=Summary)
def read_summary(
    *,
    db: Session = Depends(get_db),
    summary_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get summary by ID."""
    summary = db.query(models.Summary).filter(models.Summary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    if summary.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return summary
