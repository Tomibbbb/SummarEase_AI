import os
import time
import json
from datetime import datetime
from celery import Celery
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import SessionLocal
from app.models.summary import Summary
from app.models.usage_statistics import UsageStatistics
from app.services.cohere_service import CohereService
from app.services.s3_service import S3Service

# Initialize Celery
celery = Celery(__name__)
celery.conf.broker_url = settings.REDIS_URL
celery.conf.result_backend = settings.REDIS_URL

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
)

@celery.task(name="process_summary", bind=True, max_retries=3)
def process_summary(self, summary_id: int):
    db = SessionLocal()
    start_time = time.time()
    
    try:
        summary = db.query(Summary).filter(Summary.id == summary_id).first()
        if not summary:
            return {"error": "Summary not found", "summary_id": summary_id}
        
        summary.processing_started_at = datetime.utcnow()
        summary.status = "processing"
        db.commit()
        
        model_id = summary.model_used if summary.model_used in CohereService.MODELS else CohereService.DEFAULT_MODEL
        
        result = CohereService.get_summary(
            text=summary.original_text,
            model_id=model_id,
            max_length=summary.max_length,
            min_length=summary.min_length
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if not result.get("success"):
            summary.status = "failed"
            summary.error_message = result.get("error", "Unknown error")
        else:
            summary_text = result.get("summary", "")
            summary.summary_text = summary_text
            summary.status = "completed"
            summary.completed_at = datetime.utcnow()
            
            if "stats" in result:
                stats = result["stats"]
                summary.processing_time_ms = stats.get("processing_time_ms", processing_time_ms)
                summary.original_tokens = stats.get("input_tokens", 0)
                summary.summary_tokens = stats.get("output_tokens", 0)
                
                cost_per_1k_tokens = 0.0004
                total_tokens = (summary.original_tokens or 0) + (summary.summary_tokens or 0)
                summary.processing_cost = (total_tokens / 1000) * cost_per_1k_tokens
            else:
                summary.processing_time_ms = processing_time_ms
                
            if summary_text:
                try:
                    summary_data = {
                        "id": summary.id,
                        "summary_text": summary_text,
                        "original_text": summary.original_text,
                        "model_used": summary.model_used,
                        "processing_time_ms": summary.processing_time_ms,
                        "tokens": {
                            "input": summary.original_tokens,
                            "output": summary.summary_tokens
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    s3_key = S3Service.store_summary(summary.id, summary_data)
                    
                    if s3_key:
                        summary.s3_location = s3_key
                except Exception as s3_error:
                    print(f"Warning: Could not store summary in S3: {s3_error}")
        
        try:
            update_usage_statistics(db, summary, result.get("success", False))
        except Exception as stats_error:
            print(f"Error updating statistics: {stats_error}")
        
        db.commit()
        
        return {
            "status": summary.status,
            "summary_id": summary.id,
            "processing_time_ms": summary.processing_time_ms,
            "success": result.get("success", False)
        }
        
    except Exception as e:
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=5 * (self.request.retries + 1))
        
        try:
            if summary:
                summary.status = "failed"
                summary.error_message = f"Process error: {str(e)}"
                summary.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
            
        return {"error": str(e), "summary_id": summary_id}
        
    finally:
        db.close()

def update_usage_statistics(db: Session, summary: Summary, success: bool):
    stats = UsageStatistics.get_or_create_hourly_record(db)
    
    stats.total_requests += 1
    
    if success:
        stats.successful_requests += 1
    else:
        stats.failed_requests += 1
    
    if summary.processing_time_ms:
        if stats.avg_processing_time_ms > 0:
            total_time = stats.avg_processing_time_ms * (stats.total_requests - 1)
            stats.avg_processing_time_ms = (total_time + summary.processing_time_ms) / stats.total_requests
        else:
            stats.avg_processing_time_ms = summary.processing_time_ms
        
        if summary.processing_time_ms > stats.max_processing_time_ms:
            stats.max_processing_time_ms = summary.processing_time_ms
    
    if summary.original_tokens and summary.summary_tokens:
        stats.total_tokens_processed += (summary.original_tokens + summary.summary_tokens)
    
    if summary.processing_cost:
        stats.cohere_api_cost = getattr(stats, "cohere_api_cost", 0) + summary.processing_cost
    
    db.add(stats)
    db.commit()
