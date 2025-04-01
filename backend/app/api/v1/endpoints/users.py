from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.api import deps
from app.core.security import get_password_hash
from app.schemas.user import User, UserUpdate, UserStats

router = APIRouter()

@router.get("/me", response_model=User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user

@router.put("/me", response_model=User)
def update_user_me(
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate = Body(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    user_data = jsonable_encoder(current_user)
    update_data = user_in.dict(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field in user_data:
        if field in update_data:
            setattr(current_user, field, update_data[field])
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me/stats", response_model=UserStats)
def read_user_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    total_summaries = db.query(func.count(models.Summary.id)).filter(
        models.Summary.user_id == current_user.id
    ).scalar()
    
    pending_summaries = db.query(func.count(models.Summary.id)).filter(
        models.Summary.user_id == current_user.id,
        models.Summary.status == "pending"
    ).scalar()
    
    completed_summaries = db.query(func.count(models.Summary.id)).filter(
        models.Summary.user_id == current_user.id,
        models.Summary.status == "completed"
    ).scalar()
    
    return {
        "total_summaries": total_summaries,
        "pending_summaries": pending_summaries,
        "completed_summaries": completed_summaries,
        "credits_remaining": current_user.credits
    }

@router.post("/add-credits", response_model=User)
def add_user_credits(
    db: Session = Depends(deps.get_db),
    credits: int = Body(..., embed=True, gt=0),
    current_user: models.User = Depends(deps.get_current_admin_user),
    user_id: int = Body(...),
) -> Any:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.credits += credits
    db.commit()
    db.refresh(user)
    return user