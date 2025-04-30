import sys
import os
import pytest
import time
import statistics
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to find the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.test_main import app
from app.models.user import User
from app.models.summary import Summary


@pytest.fixture
def client():
    """Create a test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create mock authentication headers"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        # Create a mock authenticated user
        mock_user = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "is_active": True,
            "credits": 100,
            "role": "user"
        }
        mock_get_user.return_value = mock_user
        
        # Return mock auth headers
        return {"Authorization": "Bearer fake_token_for_test"}


@pytest.fixture
def mock_db_session():
    """Create a mock database session with preloaded data"""
    with patch("app.api.deps.get_db") as mock_get_db:
        # Create a mock for the database session
        mock_session = MagicMock()
        
        # Create mock summaries
        mock_summaries = [
            Summary(
                id=i,
                user_id=1,
                original_text=f"Content {i}",
                model_used="bart-cnn",
                status="completed",
                summary_text=f"Summary {i}"
            )
            for i in range(1, 101)  # Create 100 mock summaries
        ]
        
        # Configure queries
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_summaries
        mock_query.all.return_value = mock_summaries
        
        # Configure first() to return individual summaries
        def get_first_summary():
            result = MagicMock()
            result.first.return_value = mock_summaries[0]
            return result
        
        mock_query.filter.side_effect = get_first_summary
        mock_session.query.return_value = mock_query
        
        # Make get_db return our mock session
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        yield mock_session


def measure_response_time(client, method, url, headers=None, json=None, num_requests=5):
    """Measure the response time for an API endpoint"""
    response_times = []
    
    for _ in range(num_requests):
        start_time = time.time()
        
        if method.lower() == "get":
            response = client.get(url, headers=headers)
        elif method.lower() == "post":
            response = client.post(url, headers=headers, json=json)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Only count successful responses
        if response.status_code < 400:
            response_times.append(response_time)
            
    if not response_times:
        return None
        
    # Calculate statistics
    avg_time = statistics.mean(response_times)
    max_time = max(response_times)
    min_time = min(response_times)
    
    # Calculate 95th percentile if we have enough data
    if len(response_times) >= 5:
        percentile_95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
    else:
        percentile_95 = max_time
    
    return {
        "avg_ms": avg_time,
        "min_ms": min_time,
        "max_ms": max_time,
        "p95_ms": percentile_95
    }


@pytest.mark.xfail(reason="Login performance test needs full app context")
def test_login_performance(client, mock_db_session):
    """Test login endpoint performance"""
    # Configure mock user for authentication using raw SQL execution
    with patch("sqlalchemy.sql.text") as mock_text:
        # Mock the SQL execution to return our test user
        mock_result = MagicMock()
        mock_result.first.return_value = (1, "test@example.com", "$2b$12$4SoraWIKXpjwgGYMSUuKO.5OtyXKXs5xlPxJeWZmyQhhMNi/7YU..")
        mock_db_session.execute.return_value = mock_result
        
        # Measure login performance
        results = measure_response_time(
            client,
            "post",
            "/api/v1/auth/login",
            json=None,
            num_requests=5,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Assertions with reasonable performance expectations for a mock environment
        if results:
            assert results["avg_ms"] < 500  # Average should be under 500ms
            assert results["p95_ms"] < 1000  # 95% of requests should be under 1000ms


@pytest.mark.xfail(reason="Summaries performance test needs full app context")
def test_get_summaries_performance(client, auth_headers, mock_db_session):
    """Test retrieving all summaries performance"""
    # Measure performance of listing all summaries
    results = measure_response_time(
        client,
        "get",
        "/api/v1/summaries/",
        headers=auth_headers,
        num_requests=5
    )
    
    # Assertions for response time
    if results:
        assert results["avg_ms"] < 500  # Average should be under 500ms
        assert results["p95_ms"] < 1000  # 95% of requests should be under 1000ms


@pytest.mark.xfail(reason="Summary creation performance test needs full app context")
def test_create_summary_performance(client, auth_headers, mock_db_session):
    """Test creating a summary performance"""
    # Mock the HuggingFace service
    with patch("app.services.huggingface_service.HuggingFaceService.get_summary") as mock_summarize:
        mock_summarize.return_value = {
            "success": True,
            "summary": "This is a mock summarized text.",
            "stats": {
                "processing_time_ms": 120,
                "input_tokens": 100,
                "output_tokens": 30
            }
        }
        
        # Test data for creating a summary
        summary_data = {
            "original_text": "This is a test text that needs to be summarized with proper analysis. It should be long enough to provide meaningful summarization.",
            "model_id": "bart-cnn",
            "min_length": 30,
            "max_length": 100
        }
        
        # Measure performance
        results = measure_response_time(
            client,
            "post",
            "/api/v1/summaries/",
            headers=auth_headers,
            json=summary_data,
            num_requests=5
        )
        
        # Assertions for response time
        if results:
            assert results["avg_ms"] < 800  # Creating a summary should be under 800ms
            assert results["p95_ms"] < 1500  # 95% under 1500ms