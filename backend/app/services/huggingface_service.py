import requests
from app.core.config import settings

class HuggingFaceService:
    """Service for interacting with the Hugging Face API."""
    
    @staticmethod
    def get_summary(text: str):
        """Get a summary of the provided text using Hugging Face API."""
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        
        try:
            payload = {"inputs": text, "parameters": {"max_length": 150}}
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return {"success": True, "summary": result[0]["summary_text"]}
            else:
                return {"success": False, "error": "Unexpected response format"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error processing summary: {str(e)}"}
