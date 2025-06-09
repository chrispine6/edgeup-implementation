# User model for MongoDB
from pymongo.collection import Collection
from typing import Optional

class UserModel:
    def __init__(self, db):
        self.collection: Collection = db["users"]

    def create_user(self, name: str, firebase_id: str, email: Optional[str] = None) -> dict:
        user_doc = {
            "name": name,
            "firebase_id": firebase_id,
            "email": email,
        }
        result = self.collection.insert_one(user_doc)
        user_doc["_id"] = str(result.inserted_id)
        return user_doc

    def get_user_by_firebase_id(self, firebase_id: str) -> Optional[dict]:
        user = self.collection.find_one({"firebase_id": firebase_id})
        if user:
            user["_id"] = str(user["_id"])
        return user

    def update_user(self, firebase_id: str, update_fields: dict) -> bool:
        result = self.collection.update_one({"firebase_id": firebase_id}, {"$set": update_fields})
        return result.modified_count > 0

    def delete_user(self, firebase_id: str) -> bool:
        result = self.collection.delete_one({"firebase_id": firebase_id})
        return result.deleted_count > 0
