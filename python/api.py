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

from mongo_connection import client
from user_model import UserModel
from text_chunk_model import TextChunkModel
from dialogue_model import DialogueModel

class ChatQueryRequest(BaseModel):
    query: str
    user_id: str
    document_ids: Optional[List[str]] = None
    previous_dialogue_id: Optional[str] = None

class ChatQueryResponse(BaseModel):
    success: bool
    dialogue_id: str
    query: str
    response: str
    references: List[dict]
    context_chunks_count: int
    searched_documents: List[str]

logging.basicConfig(level=logging.WARNING, 
                   format='%(levelname)s: %(message)s',
                   force=True)

load_dotenv()

app = FastAPI(title="document processing api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    try:
        client.admin.command('ismaster')
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    return {"status": "ok", "mongo": mongo_status}

@app.get("/sign-in")
def sign_on(name: str = "Anonymous", firebase_id: str = "", email: str = ""):
    try:
        db = client.get_database("edgeup")
        user_model = UserModel(db)
        if not firebase_id:
            logging.warning("sign-in attempt with missing firebase_id.")
            return {"success": False, "error": "firebase_id is required"}
        user = user_model.get_user_by_firebase_id(firebase_id)
        if not user:
            user = user_model.create_user(name=name, firebase_id=firebase_id, email=email)
            created = True
            print(f"[sign-in] created new mongodb user for firebase_id={firebase_id}, email={email}")
            logging.info(f"created new mongodb user for firebase_id={firebase_id}, email={email}")
        else:
            created = False
            print(f"[sign-in] authentication successful, mongodb user exists for firebase_id={firebase_id}, email={user.get('email')}")
            logging.info(f"authentication successful, mongodb user exists for firebase_id={firebase_id}, email={user.get('email')}")
        print(f"[mongo user doc] user document: {user}")
        if user and '_id' in user:
            user = dict(user)
            user['_id'] = str(user['_id'])
        return {"success": True, "created": created, "user": user}
    except Exception as e:
        logging.error(f"sign-in error: {str(e)}")
        return {"success" : False, "error": str(e)}

@app.get("/debug-embedding")
def debug_embedding():
    try:
        result = debug_embeddings("this is a test text to check if embeddings are working correctly.")
        return {"success": result, "message": "embedding test completed successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    elif hasattr(obj, '__dict__'):
        return {k: convert_objectid_to_str(v) for k, v in obj.__dict__.items()}
    else:
        return obj

def debug_objectids(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            debug_objectids(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            debug_objectids(v, f"{path}[{i}]")
    elif isinstance(obj, ObjectId):
        print(f"found objectid at {path}: {obj}")
    return obj

@app.post("/process-sequence")
async def process_sequence(file: UploadFile = File(...), user_id: str = Form("anonymous")):
    # process a document (pdf or image) through extraction, chunking, embedding, and vector storage in sequence with detailed output
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    supported_pdf = file_extension == 'pdf'
    supported_image = file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
    if not (supported_pdf or supported_image):
        raise HTTPException(
            status_code=400, 
            detail=f"file {file.filename} is not supported. supported formats: pdf, jpg, jpeg, png, gif, bmp, tiff, webp"
        )
    file_suffix = f'.{file_extension}'
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
        temp_file_path = temp_file.name
        shutil.copyfileobj(file.file, temp_file)
    try:
        file_type = get_file_type(temp_file_path)
        print(f"\n\033[1;34mstep 1: extracting text from {file.filename} (type: {file_type})\033[0m\n")
        if file_type == 'pdf':
            pages = extract_text_from_pdf(temp_file_path)
        elif file_type == 'image':
            pages = extract_text_from_image_as_pages(temp_file_path)
        else:
            raise ValueError(f"unsupported file type: {file_type}")
        print(f"\n\033[1;34mstep 2: creating chunks from extracted text\033[0m\n")
        from doc_chunks import chunk_pages
        chunks = chunk_pages(pages, max_tokens=500, overlap=50)
        print(f"\n\033[1;34mstep 3: generating embeddings for {len(chunks)} chunks\033[0m\n")
        from embeddings import embed_chunks
        embedded_chunks = embed_chunks(chunks)
        print(f"\n\033[1;32membeddings generated for {len(embedded_chunks)} chunks.\033[0m\n")
        print(f"\n\033[1;34mstep 4: storing vectors in pinecone database\033[0m\n")
        document_id = str(uuid.uuid4())
        from pinecone_vectors import store_document_chunks
        import copy
        embedded_chunks_copy = copy.deepcopy(embedded_chunks)
        vector_count = store_document_chunks(
            embedded_chunks_copy,
            document_id=document_id,
            user_id=user_id,
            filename=file.filename
        )
        print(f"\n\033[1;32msuccessfully stored {vector_count} vectors in pinecone\033[0m\n")
        print(f"\n\033[1;34mstep 5: storing chunks in mongodb\033[0m\n")
        db = client.get_database("edgeup")
        chunk_model = TextChunkModel(db)
        mongo_inserted_count = chunk_model.insert_chunks(embedded_chunks, document_id, user_id, file.filename)
        print(f"\n\033[1;32msuccessfully stored {mongo_inserted_count} chunks in mongodb\033[0m\n")
        embedded_chunks = convert_objectid_to_str(embedded_chunks)
        pages = convert_objectid_to_str(pages)
        chunks = convert_objectid_to_str(chunks)
        sample_embedding = None
        if embedded_chunks and len(embedded_chunks) > 0 and 'embedding' in embedded_chunks[0]:
            sample_embedding = embedded_chunks[0]['embedding'][:10]
        response = {
            "success": True,
            "filename": str(file.filename),
            "document_id": str(document_id),
            "steps_completed": 5,
            "text_extraction": {
                "page_count": len(pages),
                "first_page_preview": str(pages[0][:200]) if pages else ""
            },
            "chunking": {
                "chunk_count": len(chunks),
                "first_chunk_preview": str(chunks[0]["text"][:200]) if chunks else ""
            },
            "embedding": {
                "vectors_created": len(embedded_chunks),
                "embedding_dimensions": len(embedded_chunks[0]["embedding"]) if embedded_chunks and "embedding" in embedded_chunks[0] else 0,
                "sample_embedding": sample_embedding
            },
            "vector_storage": {
                "stored_count": int(vector_count),
                "database": "pinecone",
                "document_id": str(document_id),
                "user_namespace": str(user_id)
            },
            "mongo_storage": {
                "stored_count": int(mongo_inserted_count),
                "database": "mongodb"
            }
        }
        debug_objectids(response, "response")
        response = convert_objectid_to_str(response)
        try:
            import json
            json.dumps(response, default=str)
        except Exception as e:
            print(f"error: response still contains non-serializable objects: {e}")
            response = convert_objectid_to_str(response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error processing {file.filename}: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/user-files")
def get_user_files(user_id: str = Query(...)):
    db = client.get_database("edgeup")
    chunk_model = TextChunkModel(db)
    files = chunk_model.get_files_by_user(user_id)
    files = convert_objectid_to_str(files)
    return {"success": True, "files": files}

@app.delete("/delete-file")
async def delete_file(document_id: str = Query(...), user_id: str = Query(...)):
    try:
        db = client.get_database("edgeup")
        chunk_model = TextChunkModel(db)
        doc_info = chunk_model.get_document_info(document_id, user_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="file not found or access denied")
        filename = doc_info.get('filename', 'unknown')
        print(f"\n\033[1;34mdeleting file: {filename} (document_id: {document_id})\033[0m")
        print(f"\033[1;33mstep 1: deleting chunks from mongodb...\033[0m")
        mongo_deleted_count = chunk_model.delete_chunks_by_document(document_id, user_id)
        print(f"\033[1;32mdeleted {mongo_deleted_count} chunks from mongodb\033[0m")
        print(f"\033[1;33mstep 2: deleting vectors from pinecone...\033[0m")
        from pinecone_vectors import delete_document_vectors
        pinecone_success = delete_document_vectors(document_id, user_id)
        if pinecone_success:
            print(f"\033[1;32msuccessfully deleted vectors from pinecone\033[0m")
        else:
            print(f"\033[1;31mwarning: failed to delete some vectors from pinecone\033[0m")
        print(f"\033[1;32mfile '{filename}' successfully deleted\033[0m\n")
        return {
            "success": True,
            "message": f"file '{filename}' deleted successfully",
            "mongo_deleted_count": mongo_deleted_count,
            "pinecone_success": pinecone_success,
            "document_id": document_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"\033[1;31merror deleting file: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"error deleting file: {str(e)}")

@app.post("/chat-query")
async def chat_query(
    query: str = Form(...),
    user_id: str = Form(...),
    document_ids: Optional[str] = Form(None),
    previous_dialogue_id: Optional[str] = Form(None)
):
    try:
        doc_ids_list = []
        if document_ids and document_ids.strip():
            doc_ids_list = [doc_id.strip() for doc_id in document_ids.split(",") if doc_id.strip()]
        print(f"\n\033[1;34mchat query: {query[:100]}{'...' if len(query) > 100 else ''}\033[0m")
        print(f"\033[1;34muser id: {user_id}\033[0m")
        if doc_ids_list:
            print(f"\033[1;34msearching in documents: {doc_ids_list}\033[0m")
        else:
            print(f"\033[1;34msearching in all user documents\033[0m")
        full_context_for_openai = ""
        if previous_dialogue_id:
            print(f"\033[1;35mfollow-up question detected. previous dialogue id: {previous_dialogue_id}\033[0m")
            db = client.get_database("edgeup")
            dialogue_model = DialogueModel(db)
            full_context_for_openai = dialogue_model.build_full_context_for_openailsls(previous_dialogue_id, user_id)
            print(f"\033[1;35mbuilt full conversation context ({len(full_context_for_openai)} characters)\033[0m")
        print(f"\n\033[1;33mstep 1: generating embedding for query...\033[0m")
        enhanced_query = query
        if full_context_for_openai:
            db = client.get_database("edgeup")
            dialogue_model = DialogueModel(db)
            conversation_context = dialogue_model.build_conversation_context(previous_dialogue_id, user_id)
            enhanced_query = f"{conversation_context}\n\nCurrent Question: {query}"
            print(f"\033[1;35menhanced query with conversation context for similarity search\033[0m")
        from embeddings import get_embeddings_direct
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="openai api key not configured")
        query_embedding = get_embeddings_direct(enhanced_query, api_key)
        print(f"\033[1;32mquery embedding generated (dimension: {len(query_embedding)})\033[0m")
        print(f"\n\033[1;33mstep 2: performing similarity search...\033[0m")
        from pinecone_vectors import query_document_chunks
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
            all_matches = query_document_chunks(
                query_embedding=query_embedding,
                user_id=user_id,
                document_id=None,
                top_k=10
            )
        all_matches.sort(key=lambda x: x.score, reverse=True)
        top_matches = all_matches[:8]
        print(f"\033[1;32mfound {len(top_matches)} relevant text chunks\033[0m")
        print(f"\n\033[1;33mstep 3: preparing context from similar chunks...\033[0m")
        context_chunks = []
        references = []
        for match in top_matches:
            chunk_text = match.metadata.get('text', '')
            filename = match.metadata.get('filename', 'unknown')
            page_num = match.metadata.get('page_num', 0)
            doc_id = match.metadata.get('document_id', '')
            context_chunks.append(f"[from {filename}, page {page_num}]: {chunk_text}")
            references.append({
                "text": chunk_text,
                "filename": filename,
                "page_num": page_num,
                "document_id": doc_id,
                "similarity_score": float(match.score)
            })
        context = "\n\n".join(context_chunks)
        print(f"\033[1;32mprepared context from {len(references)} chunks\033[0m")
        print(f"\n\033[1;33mstep 4: generating ai response...\033[0m")
        system_prompt = """you are a helpful ai assistant that answers questions based on the provided document context. 
        you must cite your sources in your response. when you reference information from the context, include the source in square brackets like [document.pdf, page x].
        use the exact filename and page number provided in the context.
        if the context doesn't contain enough information to answer the question fully, say so clearly.
        your response should be well-structured and informative, with proper source citations throughout."""
        user_prompt = f"""context from documents:
{context}

user question: {query}

please provide a helpful answer based on the context above. important: you must cite your sources using the format [filename, page x] whenever you reference information from the documents."""
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
        print(f"\033[1;32mai response generated ({len(ai_response)} characters)\033[0m")
        print(f"\n\033[1;33mstep 5: storing dialogue in mongodb...\033[0m")
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
        print(f"\033[1;32mdialogue stored with id: {dialogue_id}\033[0m")
        response_data = {
            "success": True,
            "dialogue_id": dialogue_id,
            "query": query,
            "response": ai_response,
            "references": references,
            "context_chunks_count": len(references),
            "searched_documents": doc_ids_list if doc_ids_list else "all_user_documents"
        }
        response_data = convert_objectid_to_str(response_data)
        print(f"\n\033[1;32mchat query completed successfully\033[0m\n")
        return response_data
    except Exception as e:
        print(f"\033[1;31merror processing chat query: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"error processing chat query: {str(e)}")

@app.get("/user-dialogues")
def get_user_dialogues(user_id: str = Query(...), limit: int = Query(50)):
    try:
        db = client.get_database("edgeup")
        dialogue_model = DialogueModel(db)
        dialogues = dialogue_model.get_user_dialogues(user_id, limit)
        dialogues = convert_objectid_to_str(dialogues)
        return {"success": True, "dialogues": dialogues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error retrieving dialogues: {str(e)}")

@app.post("/chat-query-json")
async def chat_query_json(request: ChatQueryRequest):
    try:
        query = request.query
        user_id = request.user_id
        doc_ids_list = request.document_ids or []
        previous_dialogue_id = request.previous_dialogue_id
        print(f"\n\033[1;34mchat query (json): {query[:100]}{'...' if len(query) > 100 else ''}\033[0m")
        print(f"\033[1;34muser id: {user_id}\033[0m")
        if doc_ids_list:
            print(f"\033[1;34msearching in documents: {doc_ids_list}\033[0m")
        else:
            print(f"\033[1;34msearching in all user documents\033[0m")
        conversation_context = ""
        if previous_dialogue_id:
            print(f"\033[1;35mfollow-up question detected. previous dialogue id: {previous_dialogue_id}\033[0m")
            db = client.get_database("edgeup")
            dialogue_model = DialogueModel(db)
            conversation_context = dialogue_model.build_conversation_context(previous_dialogue_id, user_id)
            print(f"\033[1;35mbuilt conversation context ({len(conversation_context)} characters)\033[0m")
        print(f"\n\033[1;33mstep 1: generating embedding for query...\033[0m")
        enhanced_query = query
        if conversation_context:
            enhanced_query = f"{conversation_context}\n\nCurrent Question: {query}"
            print(f"\033[1;35menhanced query with conversation context for similarity search\033[0m")
        from embeddings import get_embeddings_direct
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="openai api key not configured")
        query_embedding = get_embeddings_direct(enhanced_query, api_key)
        print(f"\033[1;32mquery embedding generated (dimension: {len(query_embedding)})\033[0m")
        print(f"\n\033[1;33mstep 2: performing similarity search...\033[0m")
        from pinecone_vectors import query_document_chunks
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
            all_matches = query_document_chunks(
                query_embedding=query_embedding,
                user_id=user_id,
                document_id=None,
                top_k=10
            )
        all_matches.sort(key=lambda x: x.score, reverse=True)
        top_matches = all_matches[:8]
        print(f"\033[1;32mfound {len(top_matches)} relevant text chunks\033[0m")
        if not top_matches:
            return {
                "success": True,
                "dialogue_id": None,
                "query": query,
                "response": "i couldn't find any relevant information in your uploaded documents to answer this question. please make sure you have uploaded documents that contain information related to your query.",
                "references": [],
                "context_chunks_count": 0,
                "searched_documents": doc_ids_list if doc_ids_list else []
            }
        print(f"\n\033[1;33mstep 3: preparing context from similar chunks...\033[0m")
        context_chunks = []
        references = []
        for match in top_matches:
            chunk_text = match.metadata.get('text', '')
            filename = match.metadata.get('filename', 'unknown')
            page_num = match.metadata.get('page_num', 0)
            doc_id = match.metadata.get('document_id', '')
            context_chunks.append(f"[from {filename}, page {page_num}]: {chunk_text}")
            references.append({
                "text": chunk_text,
                "filename": filename,
                "page_num": page_num,
                "document_id": doc_id,
                "similarity_score": float(match.score)
            })
        context = "\n\n".join(context_chunks)
        print(f"\033[1;32mprepared context from {len(references)} chunks\033[0m")
        print(f"\n\033[1;33mstep 4: generating ai response...\033[0m")
        system_prompt = """you are a helpful ai assistant that answers questions based on the provided document context. 
        you must cite your sources in your response. when you reference information from the context, include the source in square brackets like [document.pdf, page x].
        use the exact filename and page number provided in the context.
        if the context doesn't contain enough information to answer the question fully, say so clearly.
        your response should be well-structured and informative, with proper source citations throughout."""
        user_prompt = f"""context from documents:
{context}

user question: {query}

please provide a helpful answer based on the context above. important: you must cite your sources using the format [filename, page x] whenever you reference information from the documents."""
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
        print(f"\033[1;32mai response generated ({len(ai_response)} characters)\033[0m")
        print(f"\n\033[1;33mstep 5: storing dialogue in mongodb...\033[0m")
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
        print(f"\033[1;32mdialogue stored with id: {dialogue_id}\033[0m")
        response_data = {
            "success": True,
            "dialogue_id": dialogue_id,
            "query": query,
            "response": ai_response,
            "references": references,
            "context_chunks_count": len(references),
            "searched_documents": doc_ids_list if doc_ids_list else []
        }
        response_data = convert_objectid_to_str(response_data)
        print(f"\n\033[1;32mchat query completed successfully\033[0m\n")
        return response_data
    except Exception as e:
        print(f"\033[1;31merror processing chat query: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"error processing chat query: {str(e)}")

@app.post("/test-image-ocr")
async def test_image_ocr(file: UploadFile = File(...)):
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    supported_image = file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
    if not supported_image:
        raise HTTPException(
            status_code=400, 
            detail=f"file {file.filename} is not a supported image format. supported: jpg, jpeg, png, gif, bmp, tiff, webp"
        )
    file_suffix = f'.{file_extension}'
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
        temp_file_path = temp_file.name
        shutil.copyfileobj(file.file, temp_file)
    try:
        print(f"\n\033[1;34mtesting ocr on image: {file.filename}\033[0m\n")
        extracted_text = extract_text_from_image_as_pages(temp_file_path)
        print(f"\033[1;32msuccessfully extracted text from {file.filename}\033[0m")
        return {
            "success": True,
            "filename": file.filename,
            "extracted_text": extracted_text[0] if extracted_text else "no text found",
            "text_length": len(extracted_text[0]) if extracted_text else 0,
            "file_type": "image"
        }
    except Exception as e:
        print(f"\033[1;31merror processing image {file.filename}: {str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"error processing image {file.filename}: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    print("\n\033[1;32mstarting fastapi server on http://0.0.0.0:8000\033[0m")
    print("\033[1;32mcheck the console for embedding details when files are processed\033[0m\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="error")
