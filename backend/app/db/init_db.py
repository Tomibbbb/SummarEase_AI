from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.core.security import get_password_hash

# Create initial admin user
def create_first_admin(db: Session) -> None:
    """
    Create an admin user if no users exist in the database.
    This is useful for initial setup and testing.
    """
    admin = db.query(models.User).filter(models.User.role == "admin").first()
    if not admin:
        admin_user = models.User(
            email="admin@summarease.com",
            hashed_password=get_password_hash("admin"),  # In production, use a more secure password
            is_active=True,
            role="admin",
            credits=1000  # Admin gets more credits
        )
        db.add(admin_user)
        db.commit()

def init_db(db: Session) -> None:
    """
    Initialize the database with default data.
    """
    # Create tables if they don't exist (in dev environment)
    # In production, use proper migrations with Alembic
    
    # Create first admin user
    create_first_admin(db)