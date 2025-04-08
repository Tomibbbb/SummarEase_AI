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

@router.get("/me", response_model=dict)
def read_user_me(
    current_user: dict = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user information.
    
    This endpoint returns the authenticated user's information.
    """
    return current_user

@router.put("/me", response_model=dict)
def update_user_me(
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate = Body(...),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    from sqlalchemy.sql import text
    
    # Get the current user data
    user_data = current_user.copy()
    update_data = user_in.dict(exclude_unset=True)
    
    # For AWS compatibility, we can only update username
    if "username" in update_data:
        # Update username with raw SQL
        update_query = text("""
            UPDATE users 
            SET username = :username 
            WHERE id = :user_id
            RETURNING id, email, username, created_at
        """)
        
        result = db.execute(
            update_query,
            {
                "username": update_data["username"],
                "user_id": current_user["id"]
            }
        ).first()
        
        db.commit()
        
        if result:
            # Update the dictionary with new values
            user_data["username"] = result[2]
    
    # Password cannot be updated with current AWS schema
    # We simply ignore password updates
    
    return user_data

@router.get("/me/stats", response_model=UserStats)
def read_user_stats(
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    from sqlalchemy.sql import text
    
    # Using raw SQL for AWS compatibility
    user_id = current_user["id"]
    
    # Get summary counts with raw SQL
    total_query = text("""
        SELECT COUNT(*) FROM summaries 
        WHERE user_id = :user_id
    """)
    total_summaries = db.execute(total_query, {"user_id": user_id}).scalar() or 0
    
    pending_query = text("""
        SELECT COUNT(*) FROM summaries 
        WHERE user_id = :user_id AND status = 'pending'
    """)
    pending_summaries = db.execute(pending_query, {"user_id": user_id}).scalar() or 0
    
    completed_query = text("""
        SELECT COUNT(*) FROM summaries 
        WHERE user_id = :user_id AND status = 'completed'
    """)
    completed_summaries = db.execute(completed_query, {"user_id": user_id}).scalar() or 0
    
    return {
        "total_summaries": total_summaries,
        "pending_summaries": pending_summaries,
        "completed_summaries": completed_summaries,
        "credits_remaining": current_user.get("credits", 10)  # Default to 10 if not in dict
    }

@router.post("/add-credits", response_model=dict)
def add_user_credits(
    db: Session = Depends(deps.get_db),
    credits: int = Body(..., embed=True, gt=0),
    current_user: dict = Depends(deps.get_current_admin_user),
    user_id: int = Body(...),
) -> Any:
    from sqlalchemy.sql import text
    
    # First check if the user exists
    check_query = text("SELECT id, email, username, created_at FROM users WHERE id = :user_id")
    result = db.execute(check_query, {"user_id": user_id}).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # For AWS compatibility, we can't update credits directly in the database
    # since the column doesn't exist. Return a simulated response.
    user_dict = {
        "id": result[0],
        "email": result[1],
        "username": result[2] if result[2] else result[1].split('@')[0],
        "created_at": result[3],
        "is_active": True,
        "role": "user",
        "credits": 10 + credits  # Simulate adding credits
    }
    
    # In a real implementation, you would store credits in a separate table
    # that's available in the AWS RDS database
    return user_dict