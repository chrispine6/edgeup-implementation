import os
import argparse
import json
import tempfile
import uuid
import logging
from text_extractor import extract_text_from_pdf
from image_extractor import extract_text_from_image_as_pages
from doc_chunks import chunk_pages
from embeddings import embed_chunks
from pinecone_vectors import store_document_chunks

# Configure minimal logging
logging.basicConfig(level=logging.WARNING, 
                    format='%(levelname)s: %(message)s',
                    force=True)  # Only show warnings and errors by default

def get_file_type(file_path):
    """
    Determine the file type based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: 'pdf', 'image', or 'unknown'
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return 'pdf'
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
        return 'image'
    else:
        return 'unknown'

def process_document(file_path, output_path=None, max_tokens=500, overlap=50, user_id="anonymous"):
    """
    Process a document (PDF or image): extract text, chunk it, create embeddings, and store in Pinecone.
    """
    file_type = get_file_type(file_path)
    
    if file_type == 'unknown':
        raise ValueError(f"Unsupported file type: {file_path}")
    
    # Extract text based on file type
    if file_type == 'pdf':
        pages = extract_text_from_pdf(file_path)
    elif file_type == 'image':
        pages = extract_text_from_image_as_pages(file_path)
    
    # Chunk the text (minimal logging)
    chunks = chunk_pages(pages, max_tokens=max_tokens, overlap=overlap)
    
    # Generate embeddings - this will be logged by embeddings.py
    print("\n" + "=" * 80)
    print("\033[1;36mGENERATING EMBEDDINGS - EMBEDDING OUTPUT WILL FOLLOW:\033[0m")
    print("=" * 80 + "\n")
    
    try:
        # This function will print the embedding details
        embedded_chunks = embed_chunks(chunks)
        
        # Only log embedding summary info here
        embedding_dim = len(embedded_chunks[0]['embedding']) if embedded_chunks and 'embedding' in embedded_chunks[0] else 0
        print(f"\033[1;32mSUCCESS: Generated {len(embedded_chunks)} embeddings with dimension {embedding_dim}\033[0m")
            
    except Exception as e:
        print(f"\033[1;31mERROR GENERATING EMBEDDINGS: {str(e)}\033[0m")
        raise
    
    # Generate a unique document ID
    document_id = str(uuid.uuid4())
    filename = os.path.basename(file_path)
    
    # Store chunks in MongoDB (text_chunks collection)
    try:
        from mongo_connection import client
        from text_chunk_model import TextChunkModel
        db = client.get_database()
        chunk_model = TextChunkModel(db)
        chunk_model.insert_chunks(embedded_chunks, document_id, user_id, filename)
    except Exception as e:
        logging.warning(f"Failed to store chunks in MongoDB: {str(e)}")
    
    # Store chunks in Pinecone if we have embeddings (minimal logging)
    vector_count = 0
    if embedded_chunks:
        try:
            vector_count = store_document_chunks(
                embedded_chunks, 
                document_id=document_id, 
                user_id=user_id,
                filename=filename
            )
        except Exception as e:
            logging.error(f"Error storing vectors: {str(e)}")
    
    # Create the result object
    result = {
        "document_id": document_id,
        "filename": filename,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "vector_count": vector_count,
        "chunks": [
            {
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": chunk["embedding"] if "embedding" in chunk else None
            } for chunk in embedded_chunks
        ]
    }
    
    # Save to file if output path is provided (minimal logging)
    if output_path:
        with open(output_path, 'w') as f:
            output_result = result.copy()
            if "chunks" in output_result:
                for chunk in output_result["chunks"]:
                    if "embedding" in chunk:
                        embedding_dim = len(chunk["embedding"]) if chunk["embedding"] else 0
                        chunk["embedding"] = f"<Vector with {embedding_dim} dimensions>"
            json.dump(output_result, f, indent=2)
    
    return result

# Create a debug function to test the embeddings pipeline
def debug_embeddings(text):
    """Debug function to test the embeddings functionality"""
    chunks = [{"text": text, "metadata": {"page": 1}}]
    embedded_chunks = embed_chunks(chunks)
    if embedded_chunks and 'embedding' in embedded_chunks[0]:
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PDF documents")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output", "-o", help="Path to save output JSON")
    parser.add_argument("--max-tokens", type=int, default=500, help="Maximum tokens per chunk")
    parser.add_argument("--overlap", type=int, default=50, help="Overlapping tokens between chunks")
    parser.add_argument("--user-id", default="anonymous", help="User ID")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.info("Running in debug mode...")
        result = debug_embeddings("This is a test text to check if embeddings are working correctly.")
        logging.info(f"Debug test result: {'Success' if result else 'Failed'}")
    else:
        # Process the document
        process_document(
            args.pdf_path, 
            output_path=args.output,
            max_tokens=args.max_tokens,
            overlap=args.overlap,
            user_id=args.user_id
        )