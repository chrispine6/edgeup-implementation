import numpy as np
import sys
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def print_embedding_info(embedding, text_preview_length=50):
    # print summary information about an embedding vector in a very visible way
    emb_array = np.array(embedding)
    dim = len(embedding)
    mean = np.mean(emb_array)
    std = np.std(emb_array)
    min_val = np.min(emb_array)
    max_val = np.max(emb_array)
    print("\n" + "#" * 80)
    print("\033[1;32m>>> EMBEDDING GENERATED <<<\033[0m")
    print("#" * 80)
    print(f"\033[1mDimensions:\033[0m {dim}")
    print(f"\033[1mStatistics:\033[0m mean={mean:.6f}, std={std:.6f}, min={min_val:.6f}, max={max_val:.6f}")
    print("#" * 80 + "\n")

def get_embeddings_direct(text, api_key, model="text-embedding-3-large"):
    # generate embeddings using direct http request to avoid client initialization issues
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
    return result["data"][0]["embedding"]

def embed_chunks(chunks):
    # generate embeddings for a list of text chunks
    embedded_chunks = []
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\033[1;31mERROR: OPENAI_API_KEY environment variable is not set!\033[0m")
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    print("\n" + "!" * 100)
    print(f"\033[1;33m>>> STARTING EMBEDDING GENERATION FOR {len(chunks)} CHUNKS <<<\033[0m")
    print("!" * 100 + "\n")
    for i, chunk in enumerate(chunks):
        text_preview = chunk['text'][:50] + "..." if len(chunk['text']) > 50 else chunk['text']
        print(f"\n\033[1;33m>>> GENERATING EMBEDDING FOR CHUNK {i+1}/{len(chunks)} <<<\033[0m")
        print(f"Text: {text_preview}")
        try:
            print(f"\033[1mSending text to OpenAI API for embedding...\033[0m")
            sys.stdout.flush()
            embedding = get_embeddings_direct(chunk['text'], api_key)
            print(f"\033[1;32mReceived embedding response from OpenAI API\033[0m")
            sys.stdout.flush()
            chunk['embedding'] = embedding
            embedded_chunks.append(chunk)
            print_embedding_info(embedding)
        except Exception as e:
            print(f"\n\033[1;31mERROR GENERATING EMBEDDING: {str(e)}\033[0m")
            raise
    print("\n" + "=" * 100)
    print(f"\033[1;32m>>> EMBEDDING GENERATION COMPLETE: {len(embedded_chunks)} EMBEDDINGS GENERATED <<<\033[0m")
    print("=" * 100 + "\n")
    return embedded_chunks