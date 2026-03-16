import logging
from datetime import datetime

from google.cloud import firestore

from agent.config import settings

logger = logging.getLogger(__name__)

_db = None

def get_db():
    global _db
    if not _db:
        try:
            _db = firestore.Client(project=settings.gcp_project_id)
            logger.info("Firestore client initialized.")
        except Exception as e:
            logger.warning(f"Using mock memory. Firestore init failed: {e}")
    return _db

class MemoryManager:
    """Manages persistent memory using Firestore with rolling history."""
    
    def __init__(self):
        self.mock_db = {} # fallback for local dev without credentials
        
    def save_message(self, chat_id: int, role: str, content: str):
        db = get_db()
        message_data = {
            "role": role,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP if db else datetime.utcnow()
        }
        
        if db:
            try:
                # Store message in subcollection
                doc_ref = db.collection("conversations").document(str(chat_id))
                doc_ref.collection("messages").add(message_data)
                
                # Update last active timestamp
                doc_ref.set({"last_active": firestore.SERVER_TIMESTAMP}, merge=True)
            except Exception as e:
                logger.error(f"Failed to save message to Firestore: {e}")
        else:
            if chat_id not in self.mock_db:
                self.mock_db[chat_id] = []
            self.mock_db[chat_id].append(message_data)

    def get_recent_context(self, chat_id: int, limit: int = 10) -> list[dict]:
        db = get_db()
        if db:
            try:
                docs = (
                    db.collection("conversations")
                    .document(str(chat_id))
                    .collection("messages")
                    .order_by("timestamp", direction=firestore.Query.DESCENDING)
                    .limit(limit)
                    .stream()
                )
                # Results are descending, so we reverse them for chronological context
                messages = [doc.to_dict() for doc in docs]
                messages.reverse()
                return [{"role": m["role"], "text": m["content"]} for m in messages]
            except Exception as e:
                logger.error(f"Failed to fetch context from Firestore: {e}")
                return []
        else:
            history = self.mock_db.get(chat_id, [])
            return [{"role": m["role"], "text": m["content"]} for m in history[-limit:]]

memory_manager = MemoryManager()
