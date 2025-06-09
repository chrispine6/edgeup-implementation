# DialogueModel for MongoDB
from pymongo.collection import Collection
from typing import List, Dict, Any
from datetime import datetime

class DialogueModel:
    def __init__(self, db):
        self.collection: Collection = db["dialogues"]

    def create_dialogue(self, user_id: str, query: str, references: List[Dict[str, Any]], response: str, document_ids: List[str] = None, previous_dialogue_id: str = None) -> str:
        # create a new dialogue entry
        dialogue_doc = {
            "user_id": user_id,
            "query": query,
            "references": references,
            "response": response,
            "document_ids": document_ids or [],
            "previous_dialogue_id": previous_dialogue_id,
            "timestamp": datetime.utcnow()
        }
        result = self.collection.insert_one(dialogue_doc)
        return str(result.inserted_id)

    def get_user_dialogues(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        # get recent dialogues for a user
        return list(self.collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))

    def get_dialogue_by_id(self, dialogue_id: str, user_id: str) -> Dict[str, Any]:
        # get a specific dialogue by id (with user access check)
        from bson import ObjectId
        return self.collection.find_one({
            "_id": ObjectId(dialogue_id),
            "user_id": user_id
        })

    def delete_dialogue(self, dialogue_id: str, user_id: str) -> bool:
        # delete a dialogue (with user access check)
        from bson import ObjectId
        result = self.collection.delete_one({
            "_id": ObjectId(dialogue_id),
            "user_id": user_id
        })
        return result.deleted_count > 0

    def get_dialogue_history(self, dialogue_id: str, user_id: str) -> List[Dict[str, Any]]:
        # get the conversation history by traversing the dialogue chain backwards
        from bson import ObjectId
        dialogues = []
        current_id = dialogue_id
        while current_id:
            dialogue = self.collection.find_one({
                "_id": ObjectId(current_id),
                "user_id": user_id
            })
            if not dialogue:
                break
            dialogues.append(dialogue)
            current_id = dialogue.get("previous_dialogue_id")
        return list(reversed(dialogues))
    
    def build_conversation_context(self, previous_dialogue_id: str, user_id: str) -> str:
        # build a comprehensive context string from all previous dialogues in the conversation thread
        if not previous_dialogue_id:
            return ""
        conversation_history = self.get_dialogue_history(previous_dialogue_id, user_id)
        if not conversation_history:
            return ""
        context_parts = []
        context_parts.append("=== CONVERSATION HISTORY ===")
        all_reference_content = []
        reference_sources = set()
        for i, dialogue in enumerate(conversation_history, 1):
            context_parts.append(f"\n--- Previous Exchange {i} ---")
            context_parts.append(f"Question: {dialogue['query']}")
            context_parts.append(f"Answer: {dialogue['response']}")
            if dialogue.get('references'):
                for ref in dialogue['references']:
                    if ref.get('text'):
                        ref_id = f"{ref.get('filename', 'unknown')}_page_{ref.get('page_num', 'unknown')}"
                        if ref_id not in reference_sources:
                            reference_sources.add(ref_id)
                            ref_info = {
                                'text': ref['text'],
                                'filename': ref.get('filename', 'Unknown Document'),
                                'page_num': ref.get('page_num', 'Unknown Page'),
                                'document_id': ref.get('document_id', ''),
                                'similarity_score': ref.get('similarity_score', 0.0)
                            }
                            all_reference_content.append(ref_info)
        if all_reference_content:
            context_parts.append(f"\n=== ALL REFERENCE DOCUMENTS FROM CONVERSATION ===")
            context_parts.append(f"Total Documents Referenced: {len(all_reference_content)}")
            for i, ref in enumerate(all_reference_content, 1):
                context_parts.append(f"\n--- Reference {i} ---")
                context_parts.append(f"Source: {ref['filename']} (Page {ref['page_num']})")
                context_parts.append(f"Content: {ref['text']}")
                if ref.get('similarity_score'):
                    context_parts.append(f"Relevance: {ref['similarity_score']:.1%}")
        context_parts.append("\n=== END CONVERSATION HISTORY ===")
        return "\n".join(context_parts)
    
    def build_full_context_for_openai(self, current_query: str, previous_dialogue_id: str, user_id: str, current_references: List[Dict[str, Any]] = None) -> str:
        # build complete context for openai including conversation history and current references
        context_parts = []
        if previous_dialogue_id:
            conversation_context = self.build_conversation_context(previous_dialogue_id, user_id)
            if conversation_context:
                context_parts.append(conversation_context)
                context_parts.append("\n" + "="*50)
        context_parts.append(f"CURRENT QUESTION: {current_query}")
        if current_references:
            context_parts.append(f"\nCURRENT REFERENCES:")
            for i, ref in enumerate(current_references, 1):
                context_parts.append(f"\n--- Current Reference {i} ---")
                context_parts.append(f"Source: {ref.get('filename', 'Unknown')} (Page {ref.get('page_num', 'Unknown')})")
                context_parts.append(f"Content: {ref.get('text', '')}")
                if ref.get('similarity_score'):
                    context_parts.append(f"Relevance: {ref['similarity_score']:.1%}")
        context_parts.append(f"\nPlease provide a comprehensive answer using all available information from the conversation history and current references. If referencing previous information, please mention the source document and page.")
        return "\n".join(context_parts)
