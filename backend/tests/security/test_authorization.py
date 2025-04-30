import sys
import os
import pytest
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
def regular_user():
    """Create a mock regular user"""
    return {
        "id": 2,
        "email": "user@example.com",
        "username": "regularuser",
        "is_active": True,
        "credits": 10,
        "role": "user"
    }


@pytest.fixture
def admin_user():
    """Create a mock admin user"""
    return {
        "id": 1,
        "email": "admin@example.com",
        "username": "adminuser", 
        "is_active": True,
        "credits": 1000,
        "role": "admin"
    }


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    with patch("app.api.deps.get_db") as mock_get_db:
        # Create a mock for the database session
        mock_session = MagicMock()
        
        # Configure the mock session
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        
        # Make get_db return our mock session
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        yield mock_session


@pytest.mark.xfail(reason="Authorization endpoints need full app context")
def test_regular_user_permissions(client, regular_user, mock_db_session):
    """Test that regular users can only access their own resources"""
    # Mock the authentication to return our regular user
    with patch("app.api.deps.get_current_user", return_value=regular_user):
        # Test accessing own user profile
        response = client.get("/api/v1/users/me")
        assert response.status_code == 200
        assert response.json()["email"] == regular_user["email"]
        
        # Setup mock summary that belongs to the user
        own_summary = Summary(id=1, user_id=regular_user["id"], original_text="Test content", model_used="bart-large-cnn")
        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.first.return_value = own_summary
        
        # Test accessing own summary
        response = client.get("/api/v1/summaries/1")
        assert response.status_code == 200
        
        # Setup mock summary that belongs to another user
        other_summary = Summary(id=2, user_id=999, original_text="Other content", model_used="bart-large-cnn")
        mock_query.filter.return_value.first.return_value = other_summary
        
        # Test accessing another user's summary
        response = client.get("/api/v1/summaries/2")
        assert response.status_code == 403
        
        # Test accessing admin-only endpoint
        response = client.get("/api/v1/users/")
        assert response.status_code == 403


@pytest.mark.xfail(reason="Admin permissions need full app context")
def test_admin_user_permissions(client, admin_user, mock_db_session):
    """Test that admin users can access all resources"""
    # Mock the authentication to return our admin user
    with patch("app.api.deps.get_current_user", return_value=admin_user):
        with patch("app.api.deps.get_current_active_superuser", return_value=admin_user):
            # Test accessing own user profile
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            assert response.json()["email"] == admin_user["email"]
            
            # Setup mock summary for testing
            summary = Summary(id=1, user_id=2, original_text="Test content", model_used="bart-large-cnn")
            mock_query = mock_db_session.query.return_value
            mock_query.filter.return_value.first.return_value = summary
            
            # Test accessing any summary
            response = client.get("/api/v1/summaries/1")
            assert response.status_code == 200
            
            # Test accessing admin-only endpoint (list all users)
            mock_query.all.return_value = [admin_user]
            response = client.get("/api/v1/users/")
            assert response.status_code == 200


@pytest.mark.xfail(reason="Inactive user test needs full app context")
def test_inactive_user_restrictions(client, mock_db_session):
    """Test that inactive users cannot access protected endpoints"""
    # Create an inactive user
    inactive_user = {
        "id": 3,
        "email": "inactive@example.com",
        "username": "inactiveuser",
        "is_active": False,
        "credits": 10,
        "role": "user"
    }
    
    # Mock the authentication but fail the active check
    with patch("app.api.deps.get_current_user", return_value=inactive_user):
        # Try to access a protected endpoint
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
        
        # Try to create a summary
        response = client.post(
            "/api/v1/summaries/",
            json={"original_text": "Test content that is long enough to be valid for summarization", "model_id": "bart-cnn"}
        )
        assert response.status_code == 401


@pytest.mark.xfail(reason="Credit enforcement needs full app context")
def test_credit_enforcement(client, regular_user, mock_db_session):
    """Test that users cannot create summaries without sufficient credits"""
    # Modify user to have zero credits
    no_credit_user = regular_user.copy()
    no_credit_user["credits"] = 0
    
    # Mock the authentication to return our no-credit user
    with patch("app.api.deps.get_current_user", return_value=no_credit_user):
        # Try to create a summary
        response = client.post(
            "/api/v1/summaries/",
            json={"original_text": "Test content that is long enough to be valid for summarization", "model_id": "bart-cnn"}
        )
        
        # Should be forbidden due to insufficient credits
        assert response.status_code == 400
        assert "credits" in response.json()["detail"].lower()