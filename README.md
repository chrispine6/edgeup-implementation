# EdgeUp Implementation
AI-based document and image processing system with OCR capabilities

## System Architecture

This system consists of three main components:

1. **React Frontend**: Provides the user interface for uploading documents/images and displaying AI responses
2. **Node.js Backend**: Handles HTTP requests, file uploads, and communication with the Python service
3. **Python FastAPI Service**: Processes documents and images using OpenAI models with OCR capabilities

## Supported File Types

- **PDF Documents**: Text extraction using PyMuPDF
- **Images**: OCR text extraction using OpenAI's GPT-4 Vision model
  - Supported formats: JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP

## Setup & Installation

### Prerequisites

- Node.js (v14+)
- Python 3.8+
- npm or yarn

### Installation

1. Install server dependencies:
   ```
   cd server
   npm install
   ```

2. Install client dependencies:
   ```
   cd client
   npm install
   ```

3. Install Python dependencies:
   ```
   cd python
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Docker Deployment (Recommended)

The easiest way to run the application is using Docker:

```bash
# Quick start with Docker
./docker-deploy.sh dev

# Or for production with MongoDB
./docker-deploy.sh prod
```

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker deployment instructions.

### Option 2: Manual Development Setup

Use the included start script:

```bash
chmod +x start.sh
./start.sh
```

This will start both the Python FastAPI server and the React client.

### Option 3: Start Services Separately

1. Start the Python FastAPI service:
   ```
   cd python
   python api.py
   ```

2. Start the React client:
   ```
   cd client
   npm start
   ```

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Sign in with Google
3. Upload documents (PDF) or images (JPG, PNG, etc.) using the upload interface
4. The AI will process your files with OCR for images and text extraction for PDFs
5. Ask questions about the content in the chat interface
6. **Follow-up Questions**: After receiving a response, ask follow-up questions that will automatically reference the previous conversation context for more coherent multi-turn conversations

## API Endpoints

### Backend (Node.js) Endpoints

- `POST /api/agent/process`: Process documents with an optional query
- `POST /api/agent/query`: Process text queries without documents

### Python API Endpoints

- `GET /health`: Check if the Python service is running
- `POST /process-sequence`: Process documents/images (PDF, JPG, PNG, etc.) with full pipeline
- `POST /test-image-ocr`: Test OCR functionality on images only
- `POST /chat-query`: Process chat queries with follow-up support (form-based)
- `POST /chat-query-json`: Process chat queries with follow-up support (JSON-based)
- `GET /user-files`: Get list of uploaded files for a user
- `DELETE /delete-file`: Delete a file and its associated data

## Features

### Document & Image Processing
- **PDF Processing**: Extract text from PDF documents using PyMuPDF
- **Image OCR**: Extract text from images using OpenAI's GPT-4 Vision model
- **Multi-format Support**: JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP images
- **Intelligent Text Extraction**: Preserves formatting and structure from images
- **Unified Processing Pipeline**: Both PDFs and images go through the same chunking, embedding, and storage process

### Follow-up Questions
- **Conversation Threading**: Ask follow-up questions that reference previous conversation context
- **Context Preservation**: System combines previous query, references, and responses for enhanced relevance
- **Visual Indicators**: Clear UI feedback showing when you're in a follow-up conversation
- **Conversation History**: All dialogue interactions are stored in MongoDB with proper threading
- **Enhanced Search**: Follow-up queries benefit from expanded context for better document matching

## Troubleshooting

- **Connection Refused Error**: Make sure the Python FastAPI service is running on port 8000
- **File Upload Issues**: Check the server logs for any errors during file processing
- **OpenAI API Errors**: Verify your OpenAI API key is valid and has sufficient credits

## License

ISC
