from nltk.tokenize import sent_tokenize

def chunk_pages(pages, max_tokens=500, overlap=50):
    from tiktoken import get_encoding
    tokenizer = get_encoding("cl100k_base")

    chunks = []
    for i, page_text in enumerate(pages):
        tokens = tokenizer.encode(page_text)
        for j in range(0, len(tokens), max_tokens - overlap):
            chunk = tokenizer.decode(tokens[j:j + max_tokens])
            chunks.append({
                "text": chunk,
                "metadata": {
                    "page": i + 1
                }
            })
    return chunks
