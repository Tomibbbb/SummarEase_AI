from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.security import get_password_hash

def init_db(db: Session) -> None:
    """Initialize the database with default data."""
    try:
        print("Initializing database...")
        
        # Check if tables exist
        check_query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
        result = db.execute(check_query).scalar()
        
        if not result:
            print("Creating database tables...")
            # Create users table
            create_user_query = text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR UNIQUE,
                    username VARCHAR,
                    hashed_password VARCHAR,
                    is_active BOOLEAN DEFAULT TRUE,
                    credits INTEGER DEFAULT 10,
                    role VARCHAR DEFAULT 'user',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    api_calls_count INTEGER DEFAULT 0,
                    last_api_call TIMESTAMP WITH TIME ZONE,
                    total_usage_cost FLOAT DEFAULT 0.0
                )
            """)
            db.execute(create_user_query)
            
            # Create summaries table
            create_summaries_query = text("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    original_text TEXT,
                    summary_text TEXT,
                    status VARCHAR DEFAULT 'pending',
                    error_message VARCHAR,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processing_started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    processing_time_ms INTEGER,
                    original_tokens INTEGER,
                    summary_tokens INTEGER,
                    processing_cost FLOAT DEFAULT 0.0,
                    api_request_id VARCHAR,
                    s3_location VARCHAR,
                    model_used VARCHAR DEFAULT 'bart-cnn',
                    max_length INTEGER DEFAULT 150,
                    min_length INTEGER
                )
            """)
            db.execute(create_summaries_query)
            
            db.commit()
            print("Created database tables")
        else:
            print("Database tables already exist")
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        db.rollback()