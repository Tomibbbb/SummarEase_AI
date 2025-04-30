from app.db.base import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import sys

def create_test_user():
    """Create a test user in the database"""
    db = SessionLocal()
    
    # Check if test user already exists
    existing_user = db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        print(f"Test user 'test@example.com' already exists with ID {existing_user.id}")
        db.close()
        return
    
    # Create a new test user
    new_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("test123"),
        is_active=True,
        credits=10,
        role="user"
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"Created test user 'test@example.com' with ID {new_user.id}")
    except Exception as e:
        print(f"Error creating test user: {e}", file=sys.stderr)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()