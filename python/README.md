# Document Processing Backend

This component provides AI document processing capabilities using FastAPI and OpenAI.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```
   python document.py
   ```

The server will be available at http://localhost:8000.

## API Documentation

Once the server is running, you can access the API documentation at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## API Endpoints

- POST `/process-documents`: Process documents with a text query
- POST `/process-query`: Process a text-only query
