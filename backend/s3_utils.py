import os
import boto3
from dotenv import load_dotenv
from app.core.config import settings

# Load environment variables (mostly for local development)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Initialize S3 client with credentials from settings or environment
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=settings.AWS_REGION or os.getenv("AWS_REGION")
)

# Get bucket name from settings or environment
S3_BUCKET_NAME = settings.S3_BUCKET_NAME or os.getenv("S3_BUCKET_NAME")
