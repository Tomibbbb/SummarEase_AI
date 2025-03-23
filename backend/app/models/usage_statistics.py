from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.base import Base

class UsageStatistics(Base):
    """
    Model for tracking API usage and costs for billing and analytics purposes.
    
    This helps monitor:
    - Overall system usage patterns
    - Cost tracking across the platform
    - Rate limiting and scaling decisions
    """
    __tablename__ = "usage_statistics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time tracking
    date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    hour = Column(Integer, index=True)  # Hour of day (0-23) for hourly stats
    
    # Usage counts
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Performance metrics
    avg_processing_time_ms = Column(Float, default=0.0)
    max_processing_time_ms = Column(Float, default=0.0)
    
    # Cost tracking
    total_tokens_processed = Column(Integer, default=0)
    huggingface_api_cost = Column(Float, default=0.0)
    
    # Infrastructure stats for cost estimation
    cpu_usage_percent = Column(Float, default=0.0)
    memory_usage_mb = Column(Float, default=0.0)
    
    # Scaling metrics
    peak_concurrent_requests = Column(Integer, default=0)
    queue_depth = Column(Integer, default=0)
    
    @classmethod
    def get_or_create_hourly_record(cls, db):
        """
        Get or create a usage statistics record for the current hour.
        This is used for accumulating usage statistics.
        """
        now = func.now()
        current_hour = func.extract('hour', now)
        
        # Try to get existing record for current hour
        record = db.query(cls).filter(
            func.date_trunc('day', cls.date) == func.date_trunc('day', now),
            cls.hour == current_hour
        ).first()
        
        # Create new record if none exists
        if not record:
            record = cls(
                date=now,
                hour=current_hour,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            
        return record