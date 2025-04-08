from datetime import timedelta
from typing import Any
import requests
import json
from urllib.parse import urlencode
from fastapi import APIRouter, Body, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import text

from app import models
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import get_db
from app.schemas.token import Token
from app.schemas.user import User, UserCreate

router = APIRouter()

# Debug endpoint removed for security reasons

@router.post("/login", response_model=Token)
async def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    try:
        # Try first with password verification
        query = text("SELECT id, email, hashed_password FROM users WHERE email = :email")
        result = db.execute(query, {"email": form_data.username}).first()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        user_id, email, hashed_password = result
        
        # Check if we have a hashed password to verify
        if hashed_password and not security.verify_password(form_data.password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return {
            "access_token": security.create_access_token(
                user_id, expires_delta=access_token_expires
            ),
            "token_type": "bearer",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )


@router.post("/register", response_model=dict)
async def register_user(
    db: Session = Depends(get_db),
    email: str = Body(...),
    password: str = Body(...),
) -> Any:
    """
    Register a new user.
    """
    # Perform validation directly
    if '@' not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Password must be at least 8 characters long"
        )
    
    # Check for existing user with raw SQL for AWS compatibility
    try:
        query = text("SELECT id FROM users WHERE email = :email")
        result = db.execute(query, {"email": email}).first()
        if result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )
        
        # Create new user in database
        try:
            # Insert user with username derived from email
            insert_query = text("""
                INSERT INTO users (email, username, created_at, hashed_password, is_active, role, credits) 
                VALUES (:email, :username, now(), :hashed_password, true, 'user', :credits)
                RETURNING id, email
            """)
            result = db.execute(
                insert_query, 
                {
                    "email": email,
                    "username": email.split('@')[0],
                    "hashed_password": get_password_hash(password),
                    "credits": settings.DEFAULT_CREDITS
                }
            ).first()
        except Exception as e:
            # Handle schema variations
            if "column" in str(e) and "username" in str(e):
                insert_query = text("""
                    INSERT INTO users (email, created_at, hashed_password, is_active, role, credits) 
                    VALUES (:email, now(), :hashed_password, true, 'user', :credits)
                    RETURNING id, email
                """)
                result = db.execute(
                    insert_query, 
                    {
                        "email": email,
                        "hashed_password": get_password_hash(password),
                        "credits": settings.DEFAULT_CREDITS
                    }
                ).first()
            else:
                # Re-raise if it's another error
                raise
        
        db.commit()
        
        if not result:
            raise Exception("Failed to create user")
        
        user_id, user_email = result
        
        # Return a dictionary instead of a model to avoid ORM issues
        return {
            "id": user_id,
            "email": user_email,
            "is_active": True,
            "credits": settings.DEFAULT_CREDITS
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.post("/test-token", response_model=dict)
def test_token(current_user: dict = Depends(deps.get_current_user)) -> Any:
    return current_user

@router.post("/logout")
def logout_user() -> Any:
    """
    Log out a user.
    This is a dummy endpoint as logout is handled client-side by removing the JWT token.
    It's included for completeness in the API.
    """
    return {"success": True, "message": "Logout successful"}

@router.get("/google/login")
async def google_login():
    """
    Generate Google OAuth login URL
    """
    # Google OAuth authorization URL
    auth_url = "https://accounts.google.com/o/oauth2/auth"
    
    # Parameters for the OAuth request
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GOOGLE_SCOPES,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "select_account"
    }
    
    # Construct the full authorization URL
    auth_request_url = f"{auth_url}?{urlencode(params)}"
    
    return {"auth_url": auth_request_url}

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback
    """
    # Get the authorization code from the request
    code = request.query_params.get("code")
    if not code:
        redirect_url = f"{settings.FRONTEND_URL}?error=no_code"
        return RedirectResponse(url=redirect_url)
    
    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        }
        
        token_response = requests.post(token_url, data=token_payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        
        # Get user info with the access token
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        # Extract user's email and verified status
        email = user_info.get("email")
        verified_email = user_info.get("verified_email")
        google_id = user_info.get("id")
        name = user_info.get("name")
        
        if not email or not verified_email:
            redirect_url = f"{settings.FRONTEND_URL}?error=invalid_email"
            return RedirectResponse(url=redirect_url)
        
        # Check if user exists
        query = text("SELECT id FROM users WHERE email = :email")
        result = db.execute(query, {"email": email}).first()
        
        if not result:
            # Create new user with Google info
            try:
                # First try with username column
                username = email.split('@')[0]
                
                insert_query = text("""
                    INSERT INTO users (email, username, created_at, hashed_password, is_active, role, credits) 
                    VALUES (:email, :username, now(), :hashed_password, true, 'user', :credits)
                    RETURNING id, email
                """)
                
                # Generate a secure random password
                import secrets
                random_password = secrets.token_urlsafe(16)
                
                result = db.execute(
                    insert_query, 
                    {
                        "email": email,
                        "username": username,
                        "hashed_password": get_password_hash(random_password),
                        "credits": settings.DEFAULT_CREDITS
                    }
                ).first()
                
                db.commit()
                
            except Exception as e:
                if "column" in str(e) and "username" in str(e):
                    # Fallback if username column doesn't exist
                    insert_query = text("""
                        INSERT INTO users (email, created_at, hashed_password, is_active, role, credits) 
                        VALUES (:email, now(), :hashed_password, true, 'user', :credits)
                        RETURNING id, email
                    """)
                    
                    result = db.execute(
                        insert_query, 
                        {
                            "email": email,
                            "hashed_password": get_password_hash(random_password),
                            "credits": settings.DEFAULT_CREDITS
                        }
                    ).first()
                    
                    db.commit()
                else:
                    # Re-raise if it's another error
                    raise
            
            user_id = result[0]
        else:
            user_id = result[0]
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user_id, expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        redirect_url = f"http://localhost/dashboard.html?token={access_token}"
        
        # Set the token in a cookie too for backup
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key="access_token", 
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            expires=1800,
        )
        
        return response
        
    except requests.RequestException as e:
        # Redirect to frontend with error
        redirect_url = f"{settings.FRONTEND_URL}?error=oauth_error"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        # Redirect to frontend with error
        redirect_url = f"{settings.FRONTEND_URL}?error=server_error"
        return RedirectResponse(url=redirect_url)