# SummarEase

SummarEase is a cloud-based text summarization service powered by artificial intelligence. This application enables users to submit long text and receive concise, AI-generated summaries.

## Features

- User authentication and management
- Credit-based usage limits
- Asynchronous processing queue
- Integration with Hugging Face API for text summarization
- User notification system
- Docker deployment options (integrated or separate services)
- AWS S3 integration for storage

## Architecture

The application follows a cloud-native microservices architecture:

- Frontend: HTML/CSS/JavaScript
- Backend: FastAPI
- Database: PostgreSQL
- Queue: Redis + Celery
- External API: Hugging Face
- Storage: Local filesystem or AWS S3

## Docker Setup (Recommended)

### Option 1: Integrated Application

This runs the backend and frontend in a single container:

```bash
# Start the integrated application
chmod +x start.sh
./start.sh
```

Access the application at http://localhost:8000

### Option 2: Separate Frontend and Backend

This runs the frontend and backend in separate containers:

```bash
# Start the separate services
chmod +x start.sh
./start.sh --separate
```

Access the frontend at http://localhost:80 and the API at http://localhost:8000

## Manual Setup

### Backend

1. Install dependencies:
```
cd backend
pip install -r requirements.txt
```

2. Run the development server:
```
uvicorn main:app --reload
```

Or for the integrated version:
```
# Set up the integrated application
./setup_integrated.sh

# Run the application
cd backend
python integrated_app.py
```

## Environment Variables

The application supports the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `PROCESS_DIRECTLY`: Set to "True" to bypass task queue
- `AWS_ACCESS_KEY_ID`: AWS access key for S3 storage
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for S3 storage
- `S3_BUCKET_NAME`: S3 bucket name for storage

## Project Structure

```
SummarEase/
├── backend/        # FastAPI application
├── frontend/       # User interface
├── docs/           # Documentation
├── docker-compose.yml          # Standard Docker setup
├── docker-compose.integrated.yml # Integrated Docker setup
└── infrastructure/ # Infrastructure configuration
```

## License

[MIT License](LICENSE)