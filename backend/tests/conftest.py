import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Set test mode environment variable
os.environ["TEST_MODE"] = "true"

# Load test environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.test'), override=True)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def app_settings():
    from app.core.config import Settings
    
    test_settings = Settings(
        PROJECT_NAME="SummarEase Test",
        SECRET_KEY="testsecretkey",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        DATABASE_URL="sqlite:///:memory:",
        HUGGINGFACE_API_KEY="test_api_key",
        USERS_OPEN_REGISTRATION=True,
        DEFAULT_CREDITS=10,
        MOCK_HUGGINGFACE=True,
        AWS_ACCESS_KEY_ID="test_aws_key",
        AWS_SECRET_ACCESS_KEY="test_aws_secret",
        S3_BUCKET_NAME="test-bucket"
    )
    
    with patch("app.core.config.settings", test_settings):
        yield test_settings


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    from sqlalchemy import create_engine
    from app.db.base import Base
    
    # Create an in-memory SQLite database with SQLite-specific settings
    engine = create_engine(
        "sqlite:///:memory:", 
        # SQLite needs this for thread safety
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db(test_engine):
    """Create a fresh database session for each test"""
    from sqlalchemy.orm import sessionmaker
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def override_get_db(test_db):
    """Replace the default get_db dependency with our test db"""
    from app.db.base import get_db
    
    # Override the get_db function to return our test db
    def _get_test_db():
        try:
            yield test_db
        finally:
            pass
    
    return _get_test_db
        
        
@pytest.fixture
def mock_huggingface():
    with patch("app.services.huggingface_service.HuggingFaceService") as mock:
        instance = mock.return_value
        instance.summarize.return_value = "This is a mock summarized text."
        yield instance


@pytest.fixture
def mock_s3():
    with patch("app.services.s3_service.S3Service") as mock:
        instance = mock.return_value
        instance.upload_text.return_value = "https://test-bucket.s3.amazonaws.com/test.txt"
        instance.get_presigned_url.return_value = "https://presigned-url.example.com"
        yield instance
        

@pytest.fixture
def app(override_get_db):
    """Create a FastAPI test app with test dependencies"""
    # Import our special test version of the app
    from tests.test_main import app
    from app.api.deps import get_db
    
    # Override the dependencies
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # Clear dependency overrides after test
    app.dependency_overrides = {}


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_summary_data():
    return {
        "content": "This is a test text that needs to be summarized with proper analysis. " 
                  "It should be long enough to provide a meaningful summarization. " 
                  "The summary should capture the key points and important information.",
        "model": "bart-large-cnn",
        "min_length": 30,
        "max_length": 100
    }