from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# Shared properties
class SummaryBase(BaseModel):
    original_text: str

# Properties to receive via API on creation
class SummaryCreate(SummaryBase):
    pass

# Properties to return via API
class Summary(SummaryBase):
    id: int
    user_id: int
    summary_text: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
