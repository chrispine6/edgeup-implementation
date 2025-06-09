from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os
import shutil
import uuid
import logging
from typing import Optional, List
import uvicorn
from document_processor import debug_embeddings, get_file_type
from text_extractor import extract_text_from_pdf
from image_extractor import extract_text_from_image_as_pages
from dotenv import load_dotenv
from bson import ObjectId

# MongoDB connection import
from mongo_connection import client
from user_model import UserModel
from text_chunk_model import TextChunkModel
from dialogue_model import DialogueModel

# Pydantic models for request/response
class ChatQueryRequest(BaseModel):
    query: str
    user_id: str
    document_ids: Optional[List[str]] = None
    previous_dialogue_id: Optional[str] = None  # For follow-up questions

class ChatQueryResponse(BaseModel):
    success: bool
    dialogue_id: str
    query: str
    response: str
    references: List[dict]
    context_chunks_count: int
    searched_documents: List[str]

# Configure minimal logging
logging.basicConfig(level=logging.WARNING, 
                   format='%(levelname)s: %(message)s',
                   force=True)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Document Processing API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    # Check MongoDB connection
    try:
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    return {"status": "ok", "mongo": mongo_status}

# google sign in endpoint
# make mongo user document
@app.get("/sign-in")
def sign_on(name: str = "Anonymous", firebase_id: str = "", email: str = ""):
    try:
        db = client.get_database("edgeup")
        user_model = UserModel(db)
        # If firebase_id is not provided, fail early
        if not firebase_id:
            logging.warning("Sign-in attempt with missing firebase_id.")
            return {"success": False, "error": "firebase_id is required"}
        # Check if user already exists
        user = user_model.get_user_by_firebase_id(firebase_id)
        if not user:
            user = user_model.create_user(name=name, firebase_id=firebase_id, email=email)
            created = True
            print(f"[SIGN-IN] Created new MongoDB user for firebase_id={firebase_id}, email={email}")
            logging.info(f"Created new MongoDB user for firebase_id={firebase_id}, email={email}")
        else:
            created = False
            print(f"[SIGN-IN] Authentication successful, MongoDB user exists for firebase_id={firebase_id}, email={user.get('email')}")
            logging.info(f"Authentication successful, MongoDB user exists for firebase_id={firebase_id}, email={user.get('email')}")
        # Print the user document status to the console for debugging
        print(f"[MONGO USER DOC] User document: {user}")
        # Convert ObjectId to string for JSON serialization
        if user and '_id' in user:
            user = dict(user)
            user['_id'] = str(user['_id'])
        return {"success": True, "created": created, "user": user}
    except Exception as e:
        logging.error(f"Sign-in error: {str(e)}")
        return {"success" : False, "error": str(e)}

@app.get("/debug-embedding")
def debug_embedding():
    """Debug endpoint to test embedding functionality"""
    try:
        result = debug_embeddings("This is a test text to check if embeddings are working correctly.")
        return {"success": result, "message": "Embedding test completed successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def convert_objectid_to_str(obj):
    """Recursively convert ObjectId fields to strings for JSON serialization."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    elif hasattr(obj, '__dict__'):
        # Handle objects with __dict__ attribute
        return {k: convert_objectid_to_str(v) for k, v in obj.__dict__.items()}
    else:
        return obj

def debug_objectids(obj, path=""):
    """Debug function to find any ObjectIds in a nested structure"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            debug_objectids(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            debug_objectids(v, f"{path}[{i}]")
    elif isinstance(obj, ObjectId):
        print(f"Found ObjectId at {path}: {obj}")
    return obj

@app.post("/process-sequence")
async def process_sequence(file: UploadFile = File(...), user_id: str = Form("anonymous")):
    """Process a document (PDF or image) through extraction, chunking, embedding, and vector storage in sequence with detailed output."""
    
    # Determine file type from filename
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    # Validate file type
    supported_pdf = file_extension == 'pdf'
    supported_image = file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
    
    if not (supported_pdf or supported_image):
        raise HTTPException(
            status_code=400, 
            detail=f"File {file.filename} is not supported. Supported formats: PDF, JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP"
        )
    
    # Save the uploaded file to a temporary location with appropriate extension
    file_suffix = f'.{file_extension}'
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
        temp_file_path = temp_file.name
        shutil.copyfileobj(file.file, temp_file)
    
    try:
        # STEP 1: Extract text based on file type
        file_type = get_file_type(temp_file_path)
        print(f"\n\033[1;34mSTEP 1: Extracting text from {file.filename} (type: {file_type})\033[0m\n")
        
        if file_type == 'pdf':
            pages = extract_text_from_pdf(temp_file_path)
        elif file_type == 'image':
            pages = extract_text_from_image_as_pages(temp_file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # STEP 2: Create chunks
        print(f"\n\033[1;34mSTEP 2: Creating chunks from extracted text\033[0m\n")
        from doc_chunks import chunk_pages
        chunks = chunk_pages(pages, max_tokens=500, overlap=50)
        
        # STEP 3: Generate embeddings
        print(f"\n\033[1;34mSTEP 3: Generating embeddings for {len(chunks)} chunks\033[0m\n")
        from embeddings import embed_chunks
        embedded_chunks = embed_chunks(chunks)
        print(f"\n\033[1;32mEmbeddings generated for {len(embedded_chunks)} chunks.\033[0m\n")
        
        # STEP 4: Store in Pinecone Vector Database
        print(f"\n\033[1;34mSTEP 4: Storing vectors in Pinecone database\033[0m\n")
        document_id = str(uuid.uuid4())
        from pinecone_vectors import store_document_chunks
        # Make a deep copy of embedded_chunks before Pinecone to avoid any modifications
        import copy
        embedded_chunks_copy = copy.deepcopy(embedded_chunks)
        
        vector_count = store_document_chunks(
            embedded_chunks_copy,
            document_id=document_id,
            user_id=user_id,
            filename=file.filename
        )
        print(f"\n\033[1;32mSuccessfully stored {vector_count} vectors in Pinecone\033[0m\n")

        # STEP 5: Store chunks in MongoDB
        print(f"\n\033[1;34mSTEP 5: Storing chunks in MongoDB\033[0m\n")
        db = client.get_database("edgeup")
        chunk_model = TextChunkModel(db)
        mongo_inserted_count = chunk_model.insert_chunks(embedded_chunks, document_id, user_id, file.filename)
        print(f"\n\033[1;32mSuccessfully stored {mongo_inserted_count} chunks in MongoDB\033[0m\n")

        # Convert all data to strings to avoid any ObjectId issues
        embedded_chunks = convert_objectid_to_str(embedded_chunks)
        pages = convert_objectid_to_str(pages)
        chunks = convert_objectid_to_str(chunks)

        # For API response, we'll include first chunk embedding as sample
        sample_embedding = None
        if embedded_chunks and len(embedded_chunks) > 0 and 'embedding' in embedded_chunks[0]:
            sample_embedding = embedded_chunks[0]['embedding'][:10]  # Just return first 10 dimensions as sample
        
        response = {
            "success": True,
            "filename": str(file.filename),
            "document_id": str(document_id),  # Return the document ID for future reference
            "steps_completed": 5,  # Now 5 steps including MongoDB storage
            "text_extraction": {
                "page_count": len(pages),
                "first_page_preview": str(pages[0][:200]) if pages else ""  # First 200 chars of first page
            },
            "chunking": {
                "chunk_count": len(chunks),
                "first_chunk_preview": str(chunks[0]["text"][:200]) if chunks else ""  # First 200 chars of first chunk
            },
            "embedding": {
                "vectors_created": len(embedded_chunks),
                "embedding_dimensions": len(embedded_chunks[0]["embedding"]) if embedded_chunks and "embedding" in embedded_chunks[0] else 0,
                "sample_embedding": sample_embedding
            },
            "vector_storage": {
                "stored_count": int(vector_count),
                "database": "Pinecone",
                "document_id": str(document_id),
                "user_namespace": str(user_id)
            },
            "mongo_storage": {
                "stored_count": int(mongo_inserted_count),
                "database": "MongoDB"
            }
        }
        
        # Ensure the entire response is free of ObjectIds before returning
        # Debug: Check for any remaining ObjectIds
        debug_objectids(response, "response")
        response = convert_objectid_to_str(response)
        
        # Final check - ensure no ObjectIds remain
        try:
            import json
            json.dumps(response, default=str)  # Test serialization
        except Exception as e:
            print(f"ERROR: Response still contains non-serializable objects: {e}")
            # Force convert everything to strings as fallback
            response = convert_objectid_to_str(response)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/user-files")
def get_user_files(user_id: str = Query(...)):
    db = client.get_database("edgeup")
    chunk_model = TextChunkModel(db)
    # Aggregate unique files by document_id for the user
    files = chunk_model.get_files_by_user(user_id)
    # Convert ObjectIds to strings for JSON serialization
    files = convert_objectid_to_str(files)
    return {"success": True, "files": files}

@app.delete("/delete-file")
async def delete_file(document_id: str = Query(...), user_id: str = Query(...)):
    """Delete a file and all its associated data from both MongoDB and Pinecone"""
    try:
        db = client.get_database("edgeup")
        chunk_model = TextChunkModel(db)
        
        # Get document info before deletion (for logging)
        doc_info = chunk_model.get_document_info(document_id, user_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        
        filename = doc_info.get('filename', 'Unknown')
        
        print(f"\n\033[1;34mDELETING FILE: {filename} (document_id: {document_id})\033[0m")
        
        # Step 1: Delete chunks from MongoDB
        print(f"\033[1;33mStep 1: Deleting chunks from MongoDB...\033[0m")
        mongo_deleted_count = chunk_model.delete_chunks_by_document(document_id, user_id)
        print(f"\033[1;32mDeleted {mongo_deleted_count} chunks from MongoDB\033[0m")
        
        # Step 2: Delete vectors from Pinecone
        print(f"\033[1;33mStep 2: Deleting vectors from Pinecone...\033[0m")
        from pinecone_vectors import delete_document_vectors
        pinecone_success = delete_document_vectors(document_id, user_id)
        
        if pinecone_success:
            print(f"\033[1;32mSuccessfully deleted vectors from Pinecone\033[0m")
        else:
            print(f"\033[1;31mWarning: Failed to delete some vectors from Pinecone\033[0m")
        
        print(f"\033[1;32mFile '{filename}' successfully deleted\033[0m\n")
        
        return {
            "success": True,
            "message": f"File '{filename}' deleted successfully",
            "mongo_deleted_count": mongo_deleted_count,
            "pinecone_success": pinecone_success,
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\033[1;31mError deleting file: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.post("/chat-query")
async def chat_query(
    query: str = Form(...),
    user_id: str = Form(...),
    document_ids: Optional[str] = Form(None),  # Comma-separated document IDs
    previous_dialogue_id: Optional[str] = Form(None)  # For follow-up questions
):
    """
    Process a chat query by performing similarity search and generating AI response
    
    Args:
        query: The user's question
        user_id: The user making the query
        document_ids: Optional comma-separated list of document IDs to search within
    """
    try:
        # Parse document IDs if provided
        doc_ids_list = []
        if document_ids and document_ids.strip():
            doc_ids_list = [doc_id.strip() for doc_id in document_ids.split(",") if doc_id.strip()]
        
        print(f"\n\033[1;34mCHAT QUERY: {query[:100]}{'...' if len(query) > 100 else ''}\033[0m")
        print(f"\033[1;34mUser ID: {user_id}\033[0m")
        if doc_ids_list:
            print(f"\033[1;34mSearching in documents: {doc_ids_list}\033[0m")
        else:
            print(f"\033[1;34mSearching in all user documents\033[0m")
        
        # Check if this is a follow-up question - get full context including references
        full_context_for_openai = ""
        if previous_dialogue_id:
            print(f"\033[1;35mFollow-up question detected. Previous dialogue ID: {previous_dialogue_id}\033[0m")
            db = client.get_database("edgeup")
            dialogue_model = DialogueModel(db)
            full_context_for_openai = dialogue_model.build_full_context_for_openailsls(previous_dialogue_id, user_id)
            print(f"\033[1;35mBuilt full conversation context ({len(full_context_for_openai)} characters)\033[0m")
        
        # Step 1: Generate embedding for the query (enhanced with context for follow-ups)
        print(f"\n\033[1;33mStep 1: Generating embedding for query...\033[0m")
        
        # For follow-up questions, combine the current query with conversation context
        enhanced_query = query
        if full_context_for_openai:
            # Use just the conversation part for similarity search (not all references)
            db = client.get_database("edgeup")
            dialogue_model = DialogueModel(db)
            conversation_context = dialogue_model.build_conversation_context(previous_dialogue_id, user_id)
            enhanced_query = f"{conversation_context}\n\nCurrent Question: {query}"
            print(f"\033[1;35mEnhanced query with conversation context for similarity search\033[0m")
        from embeddings import get_embeddings_direct
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        query_embedding = get_embeddings_direct(enhanced_query, api_key)
        print(f"\033[1;32mQuery embedding generated (dimension: {len(query_embedding)})\033[0m")
        
        # Step 2: Perform similarity search in Pinecone
        print(f"\n\033[1;33mStep 2: Performing similarity search...\033[0m")
        from pinecone_vectors import query_document_chunks
        
        # If document IDs are specified, search each one separately and combine results
        all_matches = []
        if doc_ids_list:
            for doc_id in doc_ids_list:
                matches = query_document_chunks(
                    query_embedding=query_embedding,
                    user_id=user_id,
                    document_id=doc_id,
                    top_k=5
                )
                all_matches.extend(matches)
        else:
            # Search all user documents
            all_matches = query_document_chunks(
                query_embedding=query_embedding,
                user_id=user_id,
                document_id=None,
                top_k=10
            )
        
        # Sort by similarity score and take top results
        all_matches.sort(key=lambda x: x.score, reverse=True)
        top_matches = all_matches[:8]  # Take top 8 most similar chunks
        
        print(f"\033[1;32mFound {len(top_matches)} relevant text chunks\033[0m")
        
        # Step 3: Prepare context from similar chunks
        print(f"\n\033[1;33mStep 3: Preparing context from similar chunks...\033[0m")
        context_chunks = []
        references = []
        
        for match in top_matches:
            chunk_text = match.metadata.get('text', '')
            filename = match.metadata.get('filename', 'Unknown')
            page_num = match.metadata.get('page_num', 0)
            doc_id = match.metadata.get('document_id', '')
            
            context_chunks.append(f"[From {filename}, Page {page_num}]: {chunk_text}")
            references.append({
                "text": chunk_text,
                "filename": filename,
                "page_num": page_num,
                "document_id": doc_id,
                "similarity_score": float(match.score)
            })
        
        context = "\n\n".join(context_chunks)
        print(f"\033[1;32mPrepared context from {len(references)} chunks\033[0m")
        
        # Step 4: Generate AI response using OpenAI
        print(f"\n\033[1;33mStep 4: Generating AI response...\033[0m")
        
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context. 
        You MUST cite your sources in your response. When you reference information from the context, include the source in square brackets like [Document.pdf, Page X].
        Use the exact filename and page number provided in the context.
        If the context doesn't contain enough information to answer the question fully, say so clearly.
        Your response should be well-structured and informative, with proper source citations throughout."""
        
        user_prompt = f"""Context from documents:
{context}

User question: {query}

Please provide a helpful answer based on the context above. IMPORTANT: You must cite your sources using the format [filename, Page X] whenever you reference information from the documents."""

        # Use OpenAI client - new API format
        from openai import OpenAI
        client_openai = OpenAI(api_key=api_key)
        
        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        print(f"\033[1;32mAI response generated ({len(ai_response)} characters)\033[0m")
        
        # Step 5: Store the dialogue in MongoDB
        print(f"\n\033[1;33mStep 5: Storing dialogue in MongoDB...\033[0m")
        db = client.get_database("edgeup")
        dialogue_model = DialogueModel(db)
        
        dialogue_id = dialogue_model.create_dialogue(
            user_id=user_id,
            query=query,
            references=references,
            response=ai_response,
            document_ids=doc_ids_list,
            previous_dialogue_id=previous_dialogue_id
        )
        
        print(f"\033[1;32mDialogue stored with ID: {dialogue_id}\033[0m")
        
        # Prepare response
        response_data = {
            "success": True,
            "dialogue_id": dialogue_id,
            "query": query,
            "response": ai_response,
            "references": references,
            "context_chunks_count": len(references),
            "searched_documents": doc_ids_list if doc_ids_list else "all_user_documents"
        }
        
        # Convert ObjectIds to strings
        response_data = convert_objectid_to_str(response_data)
        
        print(f"\n\033[1;32mChat query completed successfully\033[0m\n")
        
        return response_data
        
    except Exception as e:
        print(f"\033[1;31mError processing chat query: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Error processing chat query: {str(e)}")

@app.get("/user-dialogues")
def get_user_dialogues(user_id: str = Query(...), limit: int = Query(50)):
    """Get recent dialogues for a user"""
    try:
        db = client.get_database("edgeup")
        dialogue_model = DialogueModel(db)
        
        dialogues = dialogue_model.get_user_dialogues(user_id, limit)
        dialogues = convert_objectid_to_str(dialogues)
        
        return {"success": True, "dialogues": dialogues}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dialogues: {str(e)}")

@app.post("/chat-query-json")
async def chat_query_json(request: ChatQueryRequest):
    """
    Process a chat query using JSON request body (alternative to form-based endpoint)
    """
    try:
        query = request.query
        user_id = request.user_id
        doc_ids_list = request.document_ids or []
        previous_dialogue_id = request.previous_dialogue_id
        
        print(f"\n\033[1;34mCHAT QUERY (JSON): {query[:100]}{'...' if len(query) > 100 else ''}\033[0m")
        print(f"\033[1;34mUser ID: {user_id}\033[0m")
        if doc_ids_list:
            print(f"\033[1;34mSearching in documents: {doc_ids_list}\033[0m")
        else:
            print(f"\033[1;34mSearching in all user documents\033[0m")
        
        # Check if this is a follow-up question
        conversation_context = ""
        if previous_dialogue_id:
            print(f"\033[1;35mFollow-up question detected. Previous dialogue ID: {previous_dialogue_id}\033[0m")
            db = client.get_database("edgeup")
            dialogue_model = DialogueModel(db)
            conversation_context = dialogue_model.build_conversation_context(previous_dialogue_id, user_id)
            print(f"\033[1;35mBuilt conversation context ({len(conversation_context)} characters)\033[0m")
        
        # Step 1: Generate embedding for the query (enhanced with context for follow-ups)
        print(f"\n\033[1;33mStep 1: Generating embedding for query...\033[0m")
        
        # For follow-up questions, combine the current query with conversation context
        enhanced_query = query
        if conversation_context:
            enhanced_query = f"{conversation_context}\n\nCurrent Question: {query}"
            print(f"\033[1;35mEnhanced query with conversation context for similarity search\033[0m")
        from embeddings import get_embeddings_direct
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        query_embedding = get_embeddings_direct(enhanced_query, api_key)
        print(f"\033[1;32mQuery embedding generated (dimension: {len(query_embedding)})\033[0m")
        
        # Step 2: Perform similarity search in Pinecone
        print(f"\n\033[1;33mStep 2: Performing similarity search...\033[0m")
        from pinecone_vectors import query_document_chunks
        
        # If document IDs are specified, search each one separately and combine results
        all_matches = []
        if doc_ids_list:
            for doc_id in doc_ids_list:
                matches = query_document_chunks(
                    query_embedding=query_embedding,
                    user_id=user_id,
                    document_id=doc_id,
                    top_k=5
                )
                all_matches.extend(matches)
        else:
            # Search all user documents
            all_matches = query_document_chunks(
                query_embedding=query_embedding,
                user_id=user_id,
                document_id=None,
                top_k=10
            )
        
        # Sort by similarity score and take top results
        all_matches.sort(key=lambda x: x.score, reverse=True)
        top_matches = all_matches[:8]  # Take top 8 most similar chunks
        
        print(f"\033[1;32mFound {len(top_matches)} relevant text chunks\033[0m")
        
        # If no matches found, return early
        if not top_matches:
            return {
                "success": True,
                "dialogue_id": None,
                "query": query,
                "response": "I couldn't find any relevant information in your uploaded documents to answer this question. Please make sure you have uploaded documents that contain information related to your query.",
                "references": [],
                "context_chunks_count": 0,
                "searched_documents": doc_ids_list if doc_ids_list else []
            }
        
        # Step 3: Prepare context from similar chunks
        print(f"\n\033[1;33mStep 3: Preparing context from similar chunks...\033[0m")
        context_chunks = []
        references = []
        
        for match in top_matches:
            chunk_text = match.metadata.get('text', '')
            filename = match.metadata.get('filename', 'Unknown')
            page_num = match.metadata.get('page_num', 0)
            doc_id = match.metadata.get('document_id', '')
            
            context_chunks.append(f"[From {filename}, Page {page_num}]: {chunk_text}")
            references.append({
                "text": chunk_text,
                "filename": filename,
                "page_num": page_num,
                "document_id": doc_id,
                "similarity_score": float(match.score)
            })
        
        context = "\n\n".join(context_chunks)
        print(f"\033[1;32mPrepared context from {len(references)} chunks\033[0m")
        
        # Step 4: Generate AI response using OpenAI
        print(f"\n\033[1;33mStep 4: Generating AI response...\033[0m")
        
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context. 
        You MUST cite your sources in your response. When you reference information from the context, include the source in square brackets like [Document.pdf, Page X].
        Use the exact filename and page number provided in the context.
        If the context doesn't contain enough information to answer the question fully, say so clearly.
        Your response should be well-structured and informative, with proper source citations throughout."""
        
        user_prompt = f"""Context from documents:
{context}

User question: {query}

Please provide a helpful answer based on the context above. IMPORTANT: You must cite your sources using the format [filename, Page X] whenever you reference information from the documents."""

        # Use OpenAI client - new API format
        from openai import OpenAI
        client_openai = OpenAI(api_key=api_key)
        
        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        print(f"\033[1;32mAI response generated ({len(ai_response)} characters)\033[0m")
        
        # Step 5: Store the dialogue in MongoDB
        print(f"\n\033[1;33mStep 5: Storing dialogue in MongoDB...\033[0m")
        db = client.get_database("edgeup")
        dialogue_model = DialogueModel(db)
        
        dialogue_id = dialogue_model.create_dialogue(
            user_id=user_id,
            query=query,
            references=references,
            response=ai_response,
            document_ids=doc_ids_list,
            previous_dialogue_id=previous_dialogue_id
        )
        
        print(f"\033[1;32mDialogue stored with ID: {dialogue_id}\033[0m")
        
        # Prepare response
        response_data = {
            "success": True,
            "dialogue_id": dialogue_id,
            "query": query,
            "response": ai_response,
            "references": references,
            "context_chunks_count": len(references),
            "searched_documents": doc_ids_list if doc_ids_list else []
        }
        
        # Convert ObjectIds to strings
        response_data = convert_objectid_to_str(response_data)
        
        print(f"\n\033[1;32mChat query completed successfully\033[0m\n")
        
        return response_data
        
    except Exception as e:
        print(f"\033[1;31mError processing chat query: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Error processing chat query: {str(e)}")

@app.post("/test-image-ocr")
async def test_image_ocr(file: UploadFile = File(...)):
    """Test endpoint for image OCR functionality without full processing pipeline."""
    
    # Validate file type
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    supported_image = file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
    
    if not supported_image:
        raise HTTPException(
            status_code=400, 
            detail=f"File {file.filename} is not a supported image format. Supported: JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP"
        )
    
    # Save the uploaded file to a temporary location
    file_suffix = f'.{file_extension}'
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
        temp_file_path = temp_file.name
        shutil.copyfileobj(file.file, temp_file)
    
    try:
        # Extract text from image
        print(f"\n\033[1;34mTesting OCR on image: {file.filename}\033[0m\n")
        extracted_text = extract_text_from_image_as_pages(temp_file_path)
        
        print(f"\033[1;32mSuccessfully extracted text from {file.filename}\033[0m")
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted_text": extracted_text[0] if extracted_text else "No text found",
            "text_length": len(extracted_text[0]) if extracted_text else 0,
            "file_type": "image"
        }
        
    except Exception as e:
        print(f"\033[1;31mError processing image {file.filename}: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Error processing image {file.filename}: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    print("\n\033[1;32mStarting FastAPI server on http://0.0.0.0:8000\033[0m")
    print("\033[1;32mCheck the console for embedding details when files are processed\033[0m\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="error")
