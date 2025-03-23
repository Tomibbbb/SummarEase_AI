from celery import Celery
import os
import requests
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import SessionLocal
from app.models.summary import Summary

celery = Celery(__name__)
celery.conf.broker_url = settings.REDIS_URL
celery.conf.result_backend = settings.REDIS_URL

@celery.task(name="process_summary")
def process_summary(summary_id: int):
    """Process a summary task asynchronously."""
    # Create a database session
    db = SessionLocal()
    try:
        # Get the summary from the database
        summary = db.query(Summary).filter(Summary.id == summary_id).first()
        if not summary:
            return {"error": "Summary not found"}
        
        # Call Hugging Face API for text summarization
        result = call_huggingface_api(summary.original_text)
        
        # Update the summary in the database
        if result.get("error"):
            summary.status = "failed"
        else:
            summary.summary_text = result.get("summary_text")
            summary.status = "completed"
            summary.completed_at = datetime.utcnow()
        
        db.commit()
        return {"status": summary.status}
    except Exception as e:
        # Handle exceptions
        summary.status = "failed"
        db.commit()
        return {"error": str(e)}
    finally:
        db.close()

def call_huggingface_api(text: str):
    """Call Hugging Face API for text summarization."""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
    
    try:
        payload = {"inputs": text, "parameters": {"max_length": 150}}
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return {"summary_text": result[0]["summary_text"]}
        else:
            return {"error": "Unexpected response format from Hugging Face API"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing summary: {str(e)}"}
