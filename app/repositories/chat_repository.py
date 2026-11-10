from bson import ObjectId
from datetime import datetime, timezone
from pymongo import DESCENDING
from app.extensions.mongo import mongo
from app.models.chat import Chat


class ChatRepository:
    """
    Repositorio para gestionar operaciones de base de datos sobre la colección 'chats'.
    """
    def __init__(self, db=None):
        self._db = db

    @property
    def collection(self):
        db = self._db or mongo.get_db()
        return db.chats

    def create(self, chat: Chat) -> Chat:
        data = chat.to_dict()
        self.collection.insert_one(data)
        return chat

    def find_by_id(self, chat_id) -> Chat | None:
        if not chat_id:
            return None
        try:
            obj_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
        except Exception:
            return None
        data = self.collection.find_one({"_id": obj_id})
        return Chat.from_dict(data) if data else None

    def find_by_user_id(self, user_id, limit: int = 50, skip: int = 0) -> list[Chat]:
        if not user_id:
            return []
        try:
            obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            return []
        cursor = self.collection.find({"user_id": obj_id}).sort("updated_at", DESCENDING).skip(skip).limit(limit)
        return [Chat.from_dict(doc) for doc in cursor]

    def count_by_user_id(self, user_id) -> int:
        if not user_id:
            return 0
        try:
            obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            return 0
        return self.collection.count_documents({"user_id": obj_id})

    def update(self, chat: Chat) -> bool:
        chat.updated_at = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"_id": chat._id},
            {"$set": {
                "title": chat.title,
                "messages": chat.messages,
                "personality_snapshot": chat.personality_snapshot,
                "personality_version": chat.personality_version,
                "updated_at": chat.updated_at,
            }}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def update_snapshot(self, chat_id, snapshot: dict, version_number: int) -> bool:
        try:
            obj_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
        except Exception:
            return False
        
        now = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"_id": obj_id},
            {"$set": {
                "personality_snapshot": snapshot,
                "personality_version": int(version_number),
                "updated_at": now,
            }}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def add_message(self, chat_id, message: dict, new_title: str = None) -> bool:
        try:
            obj_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
        except Exception:
            return False
        
        now = datetime.now(timezone.utc)
        update_doc = {
            "$push": {"messages": message},
            "$set": {"updated_at": now}
        }
        if new_title:
            update_doc["$set"]["title"] = new_title

        result = self.collection.update_one({"_id": obj_id}, update_doc)
        return result.modified_count > 0

    def delete(self, chat_id) -> bool:
        try:
            obj_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
        except Exception:
            return False
        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0
