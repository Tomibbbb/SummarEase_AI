from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Summary(Base):
    """
    Summary model to store text summarization requests and results.
    
    This model is optimized for scaling with:
    - Indexed fields for quick lookups
    - Separated large text fields for efficient storage
    - Cost and usage tracking
    """
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Text storage - using Text type for large inputs
    original_text = Column(Text)
    summary_text = Column(Text, nullable=True)  # Nullable as summary may be pending
    
    # Operational fields
    status = Column(String, default="pending", index=True)  # Options: "pending", "processing", "completed", "failed"
    error_message = Column(String, nullable=True)  # Stores error details if processing fails
    
    # Timestamps for tracking and analytics
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics and cost tracking
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process the summary
    original_tokens = Column(Integer, nullable=True)  # Count of tokens in original text
    summary_tokens = Column(Integer, nullable=True)  # Count of tokens in summary
    processing_cost = Column(Float, default=0.0)  # Cost of this specific summary
    
    # External API tracking
    api_request_id = Column(String, nullable=True)  # ID from external API for tracking
    model_used = Column(String, default="facebook/bart-large-cnn")  # Which model performed the summarization
    
    # Relationship to User
    user = relationship("User", backref="summaries")
    
    @property
    def processing_time_seconds(self):
        """Convert processing time from milliseconds to seconds for display"""
        if self.processing_time_ms:
            return self.processing_time_ms / 1000
        return None