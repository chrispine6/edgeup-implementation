# edgeUp implementation

ai document processing with ocr - upload pdfs/images, extract text, chat with your docs.

## architecture

three components:
1. **react frontend** - upload ui and chat interface
2. **python fastapi** - document processing and ai chat  
3. **mongodb** - user data and conversation storage

## supported files

- **pdfs** - text extraction with pymupdf
- **images** - ocr with openai gpt-4 vision (jpg, png, gif, bmp, tiff, webp)

## setup

### prerequisites
- node.js 14+
- python 3.8+

### install deps
```bash
# client
cd client && npm install

# python backend  
cd python && pip install -r requirements.txt
```

## running the app

### docker (recommended)
```bash
# dev environment
./docker-deploy.sh dev

# production with mongodb
./docker-deploy.sh prod
```

### manual dev setup
```bash
./start.sh
```

### separate services
```bash
# python backend
cd python && python api.py

# react frontend
cd client && npm start
```

## usage

1. go to http://localhost
2. sign in with google
3. upload pdfs or images
4. chat with your documents
5. ask follow-up questions that reference previous conversation

## api endpoints

### python fastapi
- `GET /health` - health check
- `POST /process-sequence` - upload and process files
- `POST /chat-query-json` - chat with documents  
- `GET /user-files` - list uploaded files
- `DELETE /delete-file` - remove files

## features

### document processing
- pdf text extraction with pymupdf
- image ocr with gpt-4 vision
- text chunking and vector embeddings  
- storage in pinecone + mongodb

### chat system
- semantic search across documents
- conversation history and follow-ups
- source attribution with page numbers
- document-specific queries

## docker setup

containers for frontend (nginx), backend (python), and mongodb. uses docker-compose for dev/prod environments with volumes for uploads and mongo data.

see wiki's for detailed system documentation.

## troubleshooting

- check python service running on port 8000
- verify openai api key is set
- check server logs for processing errors
