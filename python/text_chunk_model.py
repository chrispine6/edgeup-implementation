from pymongo.collection import Collection
from typing import List, Dict, Any, Optional

class TextChunkModel:
    def __init__(self, db):
        self.collection: Collection = db["text_chunks"]

    def insert_chunks(self, chunks: List[Dict[str, Any]], document_id: str, user_id: str, filename: str) -> int:
        """
        Insert a list of text chunks into the collection.
        Each chunk should be a dict with at least 'text', 'metadata', and optionally 'embedding'.
        """
        docs = []
        for idx, chunk in enumerate(chunks):
            doc = {
                "document_id": document_id,
                "user_id": user_id,
                "filename": filename,
                "chunk_index": idx,
                "text": chunk.get("text", ""),
                "metadata": chunk.get("metadata", {}),
                "embedding": chunk.get("embedding", None)
            }
            docs.append(doc)
        if docs:
            result = self.collection.insert_many(docs)
            return len(result.inserted_ids)
        return 0

    def get_files_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Return a list of unique files (by document_id) for a user.
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$document_id",
                "filename": {"$first": "$filename"},
                "document_id": {"$first": "$document_id"},
                "user_id": {"$first": "$user_id"}
            }},
            {"$project": {
                "_id": 0,
                "document_id": 1,
                "filename": 1,
                "user_id": 1
            }}
        ]
        return list(self.collection.aggregate(pipeline))

    def get_document_info(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a document for a user (returns first chunk's info).
        """
        doc = self.collection.find_one({"document_id": document_id, "user_id": user_id})
        return doc

    def delete_chunks_by_document(self, document_id: str, user_id: str) -> int:
        """
        Delete all chunks for a document and user.
        """
        result = self.collection.delete_many({"document_id": document_id, "user_id": user_id})
        return result.deleted_count
