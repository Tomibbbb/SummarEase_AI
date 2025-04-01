from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SummaryBase(BaseModel):
    """
    Base schema for summary with shared attributes.
    """
    original_text: str = Field(..., min_length=50)

class SummaryCreate(SummaryBase):
    """
    Schema for creating a new summary request.
    """
    model_id: Optional[str] = "bart-cnn"
    max_length: Optional[int] = Field(150, ge=50, le=500)
    min_length: Optional[int] = Field(None, ge=20, le=200)

class SummaryUpdate(BaseModel):
    """
    Schema for updating a summary. Admin only.
    """
    status: Optional[str] = None
    summary_text: Optional[str] = None

class SummaryInDBBase(SummaryBase):
    """
    Base schema for summary from database.
    """
    id: int
    user_id: int
    status: str
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    original_tokens: Optional[int] = None
    summary_tokens: Optional[int] = None
    processing_time_ms: Optional[int] = None
    
    model_config = {
        "from_attributes": True
    }

class Summary(SummaryInDBBase):
    """
    Schema for summary response.
    """
    summary_text: Optional[str] = None
    error_message: Optional[str] = None
    
class SummaryList(BaseModel):
    """
    Schema for list of summaries response with pagination.
    """
    total: int
    items: list[Summary]
    
    model_config = {
        "from_attributes": True
    }