from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

from app.core.config import settings

# Check if we're in a test environment
is_test = os.environ.get("TEST_MODE", "").lower() == "true"

# Create the appropriate engine based on environment
if is_test or settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration (for tests or local dev)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
    )
else:
    # PostgreSQL configuration with SSL support
    connect_args = {}
    if "sslmode=require" in settings.DATABASE_URL:
        connect_args = {"sslmode": "require"}
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        connect_args=connect_args
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()