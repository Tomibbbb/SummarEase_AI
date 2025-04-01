from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.services.huggingface_service import HuggingFaceService

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Text content
    original_text = Column(Text)
    summary_text = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String, default="pending", index=True)
    error_message = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing metrics
    processing_time_ms = Column(Integer, nullable=True)
    original_tokens = Column(Integer, nullable=True)
    summary_tokens = Column(Integer, nullable=True)
    processing_cost = Column(Float, default=0.0)
    
    # API tracking
    api_request_id = Column(String, nullable=True)
    
    # Cloud storage
    s3_location = Column(String, nullable=True)
    
    # Model configuration
    model_used = Column(String, default=HuggingFaceService.DEFAULT_MODEL)
    max_length = Column(Integer, default=150)
    min_length = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", backref="summaries")
    
    @property
    def processing_time_seconds(self):
        """Get processing time in seconds."""
        if self.processing_time_ms:
            return self.processing_time_ms / 1000
        return None
        
    @property
    def is_complete(self):
        """Check if the summary is complete."""
        return self.status == "completed"
        
    @property
    def is_failed(self):
        """Check if the summary failed."""
        return self.status == "failed"
        
    @property
    def is_processing(self):
        """Check if the summary is currently processing."""
        return self.status == "processing"
        
    @property
    def is_pending(self):
        """Check if the summary is pending processing."""
        return self.status == "pending"
        
    @property
    def model_display_name(self):
        """Get a display name for the model used."""
        if self.model_used in HuggingFaceService.MODELS:
            return HuggingFaceService.MODELS[self.model_used]["name"]
        return self.model_used