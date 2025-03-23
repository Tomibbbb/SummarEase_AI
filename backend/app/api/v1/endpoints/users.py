from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.core.security import get_password_hash
from app.db.base import get_db
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.post("/", response_model=User)
def create_user(*, db: Session = Depends(get_db), user_in: UserCreate) -> Any:
    """Create new user."""
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists.",
        )
    hashed_password = get_password_hash(user_in.password)
    db_user = models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        role=user_in.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/me", response_model=User)
def read_user_me(current_user: models.User = Depends(deps.get_current_active_user)) -> Any:
    """Get current user."""
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Update current user."""
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
