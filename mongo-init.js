// MongoDB initialization script for EdgeUp application
db = db.getSiblingDB('edgeup');

// Create collections
db.createCollection('users');
db.createCollection('text_chunks');
db.createCollection('dialogues');

// Create indexes for better performance
db.users.createIndex({ "firebase_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 });

db.text_chunks.createIndex({ "user_id": 1 });
db.text_chunks.createIndex({ "document_id": 1 });
db.text_chunks.createIndex({ "user_id": 1, "document_id": 1 });

db.dialogues.createIndex({ "user_id": 1 });
db.dialogues.createIndex({ "user_id": 1, "timestamp": -1 });
db.dialogues.createIndex({ "previous_dialogue_id": 1 });

print("EdgeUp database initialized successfully!");
