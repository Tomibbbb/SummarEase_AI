import sys
import os
import pytest
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.models.user import User
from app.core.security import get_password_hash, verify_password


@pytest.fixture
def db_session():
    class MockSession:
        def add(self, obj):
            pass
        
        def commit(self):
            pass
        
        def refresh(self, obj):
            pass
            
        def query(self, model):
            return self
            
        def filter(self, condition):
            return self
            
        def first(self):
            return None
    
    return MockSession()


def test_user_create():
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        username="testuser",
        is_active=True,
        credits=10,
        role="user"
    )
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.is_active is True
    assert user.credits == 10


def test_password_hashing():
    password = "securepassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_user_representation():
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        username="testuser",
        role="user"
    )
    
    # Just check that the string representation is there
    assert str(user) is not None
    assert isinstance(str(user), str)