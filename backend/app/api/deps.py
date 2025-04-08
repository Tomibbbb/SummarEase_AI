from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import models
from app.core import security
from app.core.config import settings
from app.db.base import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Use raw SQL for AWS compatibility
    from sqlalchemy.sql import text
    result = db.execute(text("SELECT id, email, username, created_at FROM users WHERE id = :user_id"), {"user_id": user_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create a user dictionary
    user = {
        "id": result[0],
        "email": result[1],
        "username": result[2] if len(result) > 2 else result[1].split('@')[0],
        "created_at": result[3] if len(result) > 3 else None,
        "is_active": True,
        "role": "user",
        "credits": 10
    }
    
    return user

def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

def check_user_credits(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    if current_user["credits"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Not enough credits. Please purchase more credits to continue.",
        )
    return current_user