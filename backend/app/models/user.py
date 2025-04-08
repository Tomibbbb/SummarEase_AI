from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.config import settings

class User(Base):
    __tablename__ = "users"

    # Match the AWS RDS schema - keep only the columns that exist in both
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, default="") # Added to match AWS schema
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # These will be ignored when querying the database since they don't exist in AWS RDS
    # But keeping them lets the existing code work with minimal changes
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    credits = Column(Integer, default=settings.DEFAULT_CREDITS)
    role = Column(String, default="user")
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    api_calls_count = Column(Integer, default=0)
    last_api_call = Column(DateTime(timezone=True), nullable=True)
    total_usage_cost = Column(Float, default=0.0)