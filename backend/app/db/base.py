from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create the SQLAlchemy engine with optimized pool settings for scaling
# Setting pool_size and max_overflow for horizontally scaled applications
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,  # Default number of connections to maintain in the pool
    max_overflow=20,  # Maximum number of connections to create above pool_size
    pool_timeout=30,  # Seconds to wait before timeout on connection checkout
    pool_recycle=1800,  # Recycle connections after 30 minutes to prevent stale connections
)

# Create session factory with autocommit=False to have more control over transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency for database sessions in FastAPI endpoints
def get_db():
    """
    Dependency that provides a SQLAlchemy session and handles closing it after use.
    This ensures connections are returned to the pool after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()