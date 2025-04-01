import requests
import time
from typing import Dict, Any, Optional, Tuple
from app.core.config import settings

class HuggingFaceService:
    """Service for interacting with the Hugging Face API."""
    
    MODELS = {
        "bart-cnn": {
            "url": "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
            "name": "BART CNN",
            "description": "Optimized for news article summarization",
            "max_tokens": 1024,
            "default_max_length": 150
        },
        "t5-base": {
            "url": "https://api-inference.huggingface.co/models/t5-base",
            "name": "T5 Base",
            "description": "General purpose text summarization",
            "max_tokens": 512,
            "default_max_length": 100
        },
        "pegasus": {
            "url": "https://api-inference.huggingface.co/models/google/pegasus-xsum",
            "name": "Pegasus XSum",
            "description": "Extreme summarization, very concise output",
            "max_tokens": 512,
            "default_max_length": 80
        }
    }
    
    DEFAULT_MODEL = "bart-cnn"
    
    @classmethod
    def get_summary(cls, 
                   text: str, 
                   model_id: str = DEFAULT_MODEL, 
                   max_length: int = None,
                   min_length: int = None,
                   retry_count: int = 3,
                   wait_time: int = 2) -> Dict[str, Any]:
        """
        Get a summary of the provided text using Hugging Face API.
        
        Args:
            text: The text to summarize
            model_id: The model ID to use (must be one of the keys in MODELS)
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            retry_count: Number of times to retry on failure
            wait_time: Seconds to wait between retries
            
        Returns:
            Dict with success status and either summary or error message
        """
        if not settings.HUGGINGFACE_API_KEY:
            return {"success": False, "error": "Hugging Face API key not configured"}
        
        # Validate and get model
        model = cls.MODELS.get(model_id, cls.MODELS[cls.DEFAULT_MODEL])
        
        # Set up parameters
        if not max_length:
            max_length = model["default_max_length"]
            
        # Calculate token estimate (rough approximation)
        token_estimate = len(text.split())
        if token_estimate > model["max_tokens"]:
            return {
                "success": False, 
                "error": f"Text too long (approximately {token_estimate} tokens). Maximum is {model['max_tokens']} tokens."
            }
            
        # Prepare API request
        api_url = model["url"]
        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        parameters = {"max_length": max_length}
        
        if min_length:
            parameters["min_length"] = min_length
            
        payload = {"inputs": text, "parameters": parameters}
        
        # Try API request with retries
        attempt = 0
        last_error = None
        
        while attempt < retry_count:
            try:
                start_time = time.time()
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                processing_time = int((time.time() - start_time) * 1000)  # milliseconds
                
                # Check for model loading status
                if response.status_code == 503 and "loading" in response.text.lower():
                    # Model is loading, wait and retry
                    time.sleep(wait_time)
                    attempt += 1
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                # Process result based on model response format
                if isinstance(result, list) and len(result) > 0:
                    summary_text = result[0]["summary_text"]
                    
                    # Calculate token counts
                    input_tokens = token_estimate
                    output_tokens = len(summary_text.split())
                    
                    return {
                        "success": True, 
                        "summary": summary_text,
                        "model": model["name"],
                        "stats": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "processing_time_ms": processing_time
                        }
                    }
                else:
                    last_error = "Unexpected response format"
                    
            except requests.exceptions.RequestException as e:
                last_error = f"API request failed: {str(e)}"
                
            except Exception as e:
                last_error = f"Error processing summary: {str(e)}"
                
            # Wait before retrying
            time.sleep(wait_time)
            attempt += 1
            
        # All retries failed
        return {"success": False, "error": last_error}
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get the list of available models and their configurations."""
        return cls.MODELS
