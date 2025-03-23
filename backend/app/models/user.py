from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.config import settings

class User(Base):
    """
    User model to store authentication information and credit balances
    
    This model is designed for scaling with optimized indices on frequently queried fields.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    credits = Column(Integer, default=settings.DEFAULT_CREDITS)  # Initial credit allocation
    role = Column(String, default="user")  # Options: "user", "admin"
    
    # Timestamps with timezone awareness for distributed systems
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Usage statistics for analytics and rate limiting
    api_calls_count = Column(Integer, default=0)
    last_api_call = Column(DateTime(timezone=True), nullable=True)
    
    # Cost tracking 
    total_usage_cost = Column(Float, default=0.0)  # Tracks accumulated usage cost