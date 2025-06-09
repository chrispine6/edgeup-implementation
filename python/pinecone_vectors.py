import os
import time
from typing import List, Dict, Any
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("pinecone_api_key environment variable is not set")

pc = Pinecone(api_key=api_key)

INDEX_NAME = "doc-ai"

def ensure_index_exists(dimension: int = 3072):
    # make sure the pinecone index exists, creating it if necessary
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"creating pinecone index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=dimension,
            metric="cosine"
        )
        time.sleep(1)
    return pc.Index(INDEX_NAME)

def store_document_chunks(
    chunks: List[Dict[str, Any]], 
    document_id: str, 
    user_id: str,
    filename: str
) -> int:
    # store document chunks in pinecone
    index = ensure_index_exists()
    vectors = []
    for i, chunk in enumerate(chunks):
        vector_id = f"{document_id}_chunk_{i}"
        metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "page_num": chunk["metadata"].get("page", 0),
            "chunk_index": i,
            "text": chunk["text"],
            "timestamp": time.time()
        }
        vectors.append({
            "id": vector_id,
            "values": chunk["embedding"],
            "metadata": metadata
        })
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch, namespace=user_id)
    return len(vectors)

def query_document_chunks(
    query_embedding: List[float],
    user_id: str,
    document_id: str = None,
    top_k: int = 5
) -> List[Dict]:
    # query for similar chunks
    index = ensure_index_exists()
    filter_dict = None
    if document_id:
        filter_dict = {"document_id": {"$eq": document_id}}
    results = index.query(
        vector=query_embedding,
        namespace=user_id,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict
    )
    return results.matches

def delete_document_vectors(document_id: str, user_id: str) -> bool:
    # delete all vectors for a specific document from pinecone
    try:
        index = ensure_index_exists()
        dummy_vector = [0.0] * 3072
        results = index.query(
            vector=dummy_vector,
            namespace=user_id,
            top_k=10000,
            include_metadata=True,
            filter={"document_id": {"$eq": document_id}}
        )
        vector_ids = [match.id for match in results.matches]
        if vector_ids:
            batch_size = 1000
            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i:i+batch_size]
                index.delete(ids=batch, namespace=user_id)
            print(f"deleted {len(vector_ids)} vectors for document {document_id}")
            return True
        else:
            print(f"no vectors found for document {document_id}")
            return True
    except Exception as e:
        print(f"error deleting vectors for document {document_id}: {str(e)}")
        return False