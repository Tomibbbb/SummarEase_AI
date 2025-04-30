import requests
import time
from typing import Dict, Any
from app.core.config import settings

class CohereService:
    DEFAULT_MODEL = "summarize-xlarge"
    API_ENDPOINT = "https://api.cohere.ai/v1/summarize"
    
    MODELS = {
        "summarize-xlarge": {
            "name": "Summarize XLarge",
            "description": "Produces high-quality summaries of long texts",
            "default_max_length": 150
        }
    }
    
    @classmethod
    def get_summary(cls, text: str, model_id: str = DEFAULT_MODEL, 
                   max_length: int = None, min_length: int = None,
                   retry_count: int = 3, wait_time: int = 2) -> Dict[str, Any]:
        if not settings.COHERE_API_KEY:
            return {"success": False, "error": "Cohere API key not configured"}
            
        headers = {
            "Authorization": f"Bearer {settings.COHERE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model": model_id,
            "length": "short", 
            "format": "paragraph",
            "extractiveness": "high",
            "temperature": 0.3
        }
        
        attempt = 0
        last_error = None
        
        while attempt < retry_count:
            try:
                start_time = time.time()
                response = requests.post(
                    cls.API_ENDPOINT, 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )
                processing_time = int((time.time() - start_time) * 1000)
                
                response.raise_for_status()
                result = response.json()
                
                if "summary" in result:
                    summary_text = result["summary"]
                    input_tokens = len(text.split())
                    output_tokens = len(summary_text.split())
                    
                    return {
                        "success": True, 
                        "summary": summary_text,
                        "model": model_id,
                        "stats": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "processing_time_ms": processing_time
                        }
                    }
                else:
                    last_error = f"Unexpected response format: {result}"
                    
            except requests.exceptions.Timeout:
                last_error = "API request timed out"
                
            except requests.exceptions.ConnectionError:
                last_error = "Connection error, please check your network"
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                if status_code >= 500:
                    last_error = f"Server error: {e.response.text}"
                elif status_code == 429:
                    last_error = "Rate limit exceeded"
                elif status_code == 401:
                    last_error = "Unauthorized: Invalid API key"
                else:
                    last_error = f"HTTP error {status_code}: {e.response.text}"
                
            except requests.exceptions.RequestException as e:
                last_error = f"API request failed: {str(e)}"
                
            except Exception as e:
                last_error = f"Error processing summary: {str(e)}"
                
            time.sleep(wait_time * (attempt + 1))
            attempt += 1
            
        return {"success": False, "error": last_error}
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        return cls.MODELS