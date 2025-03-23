# SummarEase

SummarEase is a cloud-based text summarization service powered by artificial intelligence. This application enables users to submit long text and receive concise, AI-generated summaries.

## Features

- User authentication and management
- Credit-based usage limits
- Asynchronous processing queue
- Integration with Hugging Face API for text summarization
- User notification system

## Architecture

The application follows a cloud-native microservices architecture:

- Frontend: React or HTML/JS
- Backend: FastAPI
- Database: PostgreSQL
- Queue: Redis + Celery
- External API: Hugging Face

## Setup

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

## Project Structure

```
SummarEase/
├── backend/        # FastAPI application
├── frontend/       # User interface
└── docs/           # Documentation
```

## License

[MIT License](LICENSE)