import os
import time
from typing import List, Dict, Any
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Pinecone client
api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("PINECONE_API_KEY environment variable is not set")

# Create Pinecone instance using the new API
pc = Pinecone(api_key=api_key)

# Set the index name
INDEX_NAME = "doc-ai"

def ensure_index_exists(dimension: int = 3072):
    """Make sure the Pinecone index exists, creating it if necessary"""
    # Check if index exists
    if INDEX_NAME not in pc.list_indexes().names():
        # Only log when creating a new index
        print(f"Creating Pinecone index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=dimension,
            metric="cosine"
        )
        # Wait for index to be initialized
        time.sleep(1)
    
    # Get the index
    return pc.Index(INDEX_NAME)

def store_document_chunks(
    chunks: List[Dict[str, Any]], 
    document_id: str, 
    user_id: str,
    filename: str
) -> int:
    """Store document chunks in Pinecone"""
    index = ensure_index_exists()
    
    # Prepare vectors with IDs and metadata
    vectors = []
    for i, chunk in enumerate(chunks):
        # Create a unique ID for each vector
        vector_id = f"{document_id}_chunk_{i}"
        
        # Extract metadata from the chunk and add additional context
        metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "page_num": chunk["metadata"].get("page", 0),
            "chunk_index": i,
            "text": chunk["text"],
            "timestamp": time.time()
        }
        
        # Add to vectors list
        vectors.append({
            "id": vector_id,
            "values": chunk["embedding"],
            "metadata": metadata
        })
    
    # Upsert in batches of 100 to avoid hitting API limits (no logging)
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
    """Query for similar chunks"""
    index = ensure_index_exists()
    
    # Set up filter if document_id is provided
    filter_dict = None
    if document_id:
        filter_dict = {"document_id": {"$eq": document_id}}
    
    # Execute the query (no logging)
    results = index.query(
        vector=query_embedding,
        namespace=user_id,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict
    )
    
    return results.matches

def delete_document_vectors(document_id: str, user_id: str) -> bool:
    """Delete all vectors for a specific document from Pinecone"""
    try:
        index = ensure_index_exists()
        
        # Get all vector IDs for this document
        # First, query to get all vectors with this document_id
        # We need to use a dummy query vector to search, but we'll use filter to get all chunks
        dummy_vector = [0.0] * 3072  # Create a dummy vector of the right dimension
        
        # Query with high top_k to get all chunks for this document
        results = index.query(
            vector=dummy_vector,
            namespace=user_id,
            top_k=10000,  # High number to get all chunks
            include_metadata=True,
            filter={"document_id": {"$eq": document_id}}
        )
        
        # Extract vector IDs
        vector_ids = [match.id for match in results.matches]
        
        if vector_ids:
            # Delete vectors in batches
            batch_size = 1000
            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i:i+batch_size]
                index.delete(ids=batch, namespace=user_id)
            
            print(f"Deleted {len(vector_ids)} vectors for document {document_id}")
            return True
        else:
            print(f"No vectors found for document {document_id}")
            return True
            
    except Exception as e:
        print(f"Error deleting vectors for document {document_id}: {str(e)}")
        return False