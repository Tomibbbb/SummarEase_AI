import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from main import app
from app.core.security import get_password_hash
from app.models.user import User


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_db_session(test_db, request):
    """Use a real SQLite test database instead of mocking"""
    # Create different IDs for each test to avoid integrity errors
    test_id = hash(request.node.name) % 1000 + 100  # Generate a semi-random ID based on test name
    
    # Check if user already exists
    existing_user = test_db.query(User).filter(User.email == "test@example.com").first()
    if not existing_user:
        # Create a test user in the database
        test_user = User(
            id=test_id,
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            username="testuser",
            is_active=True,
            credits=10,
            role="user"
        )
        
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)
    
    # Special handling for inactive user test
    if request.node.name == "test_login_inactive_user":
        user = test_db.query(User).filter(User.email == "test@example.com").first()
        if user:
            user.is_active = False
            test_db.commit()
    
    yield test_db


def test_login(client, mock_db_session):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_bad_credentials(client, mock_db_session):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_inactive_user(client, mock_db_session):
    # The fixture already sets the user to inactive for this test
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    
    # Check for appropriate error response
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_current_user(client, mock_db_session):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["is_active"] is True


def test_oauth_login():
    pass