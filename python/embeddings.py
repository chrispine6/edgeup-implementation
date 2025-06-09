import numpy as np
import sys
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_embedding_info(embedding, text_preview_length=50):
    """
    Print summary information about an embedding vector in a very visible way
    
    Args:
        embedding: The embedding vector to analyze
        text_preview_length: Length of text preview to show
    """
    # Convert to numpy array for easier analysis
    emb_array = np.array(embedding)
    
    # Calculate statistics
    dim = len(embedding)
    mean = np.mean(emb_array)
    std = np.std(emb_array)
    min_val = np.min(emb_array)
    max_val = np.max(emb_array)
    
    # Print directly to console with very clear visibility
    print("\n" + "#" * 80)
    print("\033[1;32m>>> EMBEDDING GENERATED <<<\033[0m")  # Bold green text
    print("#" * 80)
    print(f"\033[1mDimensions:\033[0m {dim}")
    print(f"\033[1mStatistics:\033[0m mean={mean:.6f}, std={std:.6f}, min={min_val:.6f}, max={max_val:.6f}")
    print("#" * 80 + "\n")
    # No full embedding print, no file save

def get_embeddings_direct(text, api_key, model="text-embedding-3-large"):
    """
    Generate embeddings using direct HTTP request to avoid client initialization issues
    
    Args:
        text: Text to embed
        api_key: OpenAI API key
        model: Embedding model to use
        
    Returns:
        Embedding vector
    """
    # Replace newlines which can break things
    text = text.replace("\n", " ")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "input": text,
        "model": model
    }
    
    response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    
    result = response.json()
    
    # Extract embedding from response
    return result["data"][0]["embedding"]

def embed_chunks(chunks):
    """
    Generate embeddings for a list of text chunks
    
    Args:
        chunks: List of chunk objects with text and metadata
        
    Returns:
        List of chunk objects with embeddings added
    """
    embedded_chunks = []
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\033[1;31mERROR: OPENAI_API_KEY environment variable is not set!\033[0m")
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    print("\n" + "!" * 100)
    print(f"\033[1;33m>>> STARTING EMBEDDING GENERATION FOR {len(chunks)} CHUNKS <<<\033[0m")
    print("!" * 100 + "\n")
    
    for i, chunk in enumerate(chunks):
        text_preview = chunk['text'][:50] + "..." if len(chunk['text']) > 50 else chunk['text']
        print(f"\n\033[1;33m>>> GENERATING EMBEDDING FOR CHUNK {i+1}/{len(chunks)} <<<\033[0m")  # Bold yellow text
        print(f"Text: {text_preview}")
        
        try:
            # Direct console output before API call
            print(f"\033[1mSending text to OpenAI API for embedding...\033[0m")
            sys.stdout.flush()  # Force output to console
            
            # Use direct HTTP request instead of OpenAI client
            embedding = get_embeddings_direct(chunk['text'], api_key)
            
            # Direct console output after API call
            print(f"\033[1;32mReceived embedding response from OpenAI API\033[0m")
            sys.stdout.flush()  # Force output to console
            
            chunk['embedding'] = embedding
            embedded_chunks.append(chunk)
            
            # Print embedding information with high visibility
            print_embedding_info(embedding)
            
        except Exception as e:
            print(f"\n\033[1;31mERROR GENERATING EMBEDDING: {str(e)}\033[0m")  # Bold red text for errors
            raise
    
    # Final summary
    print("\n" + "=" * 100)
    print(f"\033[1;32m>>> EMBEDDING GENERATION COMPLETE: {len(embedded_chunks)} EMBEDDINGS GENERATED <<<\033[0m")
    print("=" * 100 + "\n")
    
    return embedded_chunks