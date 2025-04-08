from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.security import get_password_hash

# Skip admin user creation - not compatible with AWS RDS schema
def init_db(db: Session) -> None:
    """
    Initialize the database with default data.
    """
    try:
        # Try to create tables
        print("Initializing database...")
        
        # Check if tables exist
        check_query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
        result = db.execute(check_query).scalar()
        
        if not result:
            print("Tables don't exist, creating them...")
            # Create users table with the exact column structure used in AWS RDS
            create_user_query = text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR UNIQUE,
                    username VARCHAR,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            db.execute(create_user_query)
            
            # Create summaries table
            create_summaries_query = text("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    title VARCHAR,
                    original_text TEXT,
                    summary_text TEXT,
                    original_file_path VARCHAR,
                    status VARCHAR DEFAULT 'pending',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                )
            """)
            db.execute(create_summaries_query)
            
            db.commit()
            print("Created database tables")
        else:
            print("Tables already exist, checking schema...")
            
            # Check if username column exists in users table
            check_column_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'username'
                )
            """)
            has_username_column = db.execute(check_column_query).scalar()
            
            if not has_username_column:
                print("Adding username column to users table")
                add_column_query = text("ALTER TABLE users ADD COLUMN username VARCHAR")
                db.execute(add_column_query)
                db.commit()
                print("Added username column")
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        db.rollback()