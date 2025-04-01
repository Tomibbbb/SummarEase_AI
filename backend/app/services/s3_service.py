import json
import time
import uuid
from typing import Dict, Any, Optional

from s3_utils import s3_client, S3_BUCKET_NAME

class S3Service:
    """
    Service for handling S3 operations related to summaries.
    
    This service provides methods for storing and retrieving summaries
    from Amazon S3 storage, which allows for cost-effective storage
    of summary data especially when dealing with large volumes.
    """
    
    @staticmethod
    def store_summary(summary_id: int, content: Dict[str, Any]) -> Optional[str]:
        """
        Store a summary in S3.
        
        Args:
            summary_id: The database ID of the summary
            content: Dictionary with summary data to store
            
        Returns:
            The S3 key where the summary is stored, or None if failed
        """
        if not S3_BUCKET_NAME:
            return None
            
        try:
            # Generate a unique key for the summary
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            key = f"summaries/{summary_id}/{timestamp}_{unique_id}.json"
            
            # Convert content to JSON
            content_json = json.dumps(content)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=key,
                Body=content_json,
                ContentType='application/json'
            )
            
            return key
            
        except Exception as e:
            print(f"Error storing summary in S3: {e}")
            return None
    
    @staticmethod
    def get_summary(s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a summary from S3.
        
        Args:
            s3_key: The S3 key where the summary is stored
            
        Returns:
            Dictionary with summary data or None if retrieval failed
        """
        if not S3_BUCKET_NAME or not s3_key:
            return None
            
        try:
            response = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key
            )
            
            # Read and parse the JSON content
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
            
        except Exception as e:
            print(f"Error retrieving summary from S3: {e}")
            return None
    
    @staticmethod
    def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for accessing a summary.
        
        Args:
            s3_key: The S3 key where the summary is stored
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if generation failed
        """
        if not S3_BUCKET_NAME or not s3_key:
            return None
            
        try:
            url = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': S3_BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            
            return url
            
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    @staticmethod
    def delete_summary(s3_key: str) -> bool:
        """
        Delete a summary from S3.
        
        Args:
            s3_key: The S3 key where the summary is stored
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not S3_BUCKET_NAME or not s3_key:
            return False
            
        try:
            s3_client.delete_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key
            )
            
            return True
            
        except Exception as e:
            print(f"Error deleting summary from S3: {e}")
            return False