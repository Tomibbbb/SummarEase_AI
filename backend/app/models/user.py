from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.config import settings

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    credits = Column(Integer, default=settings.DEFAULT_CREDITS)
    role = Column(String, default="user")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    api_calls_count = Column(Integer, default=0)
    last_api_call = Column(DateTime(timezone=True), nullable=True)
    
    total_usage_cost = Column(Float, default=0.0)