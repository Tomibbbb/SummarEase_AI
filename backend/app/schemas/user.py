from typing import Optional, Annotated
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr

class UserBase(BaseModel):
    """
    Base user schema with shared attributes.
    """
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    role: Optional[str] = "user"

class UserCreate(UserBase):
    """
    Schema for user registration.
    """
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserUpdate(UserBase):
    """
    Schema for updating user information.
    """
    password: Optional[str] = Field(None, min_length=8)

class UserInDBBase(UserBase):
    """
    Base schema for user from database.
    """
    id: int
    credits: int
    
    model_config = {
        "from_attributes": True
    }

class User(UserInDBBase):
    """
    Schema for user response.
    """
    pass

class UserInDB(UserInDBBase):
    """
    Schema for user with hashed password.
    Internal use only.
    """
    hashed_password: str
    
class UserStats(BaseModel):
    """
    Schema for user statistics response.
    """
    total_summaries: int
    pending_summaries: int
    completed_summaries: int
    credits_remaining: int
    
    model_config = {
        "from_attributes": True
    }