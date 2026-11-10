from bson import ObjectId
from datetime import datetime, timezone
from app.extensions.mongo import mongo
from app.models.interaction import Interaction


class InteractionRepository:
    """
    Repositorio para gestionar interacciones (likes de personalidades).
    """
    def __init__(self, db=None):
        self._db = db

    @property
    def collection(self):
        db = self._db or mongo.get_db()
        return db.interactions

    def add_like(self, user_id, personality_id) -> bool:
        try:
            u_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            p_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return False

        # Usar update con upsert para garantizar idempotencia
        try:
            interaction = Interaction(user_id=u_id, personality_id=p_id, type="like")
            self.collection.update_one(
                {"user_id": u_id, "personality_id": p_id, "type": "like"},
                {"$setOnInsert": interaction.to_dict()},
                upsert=True
            )
            return True
        except Exception:
            return False

    def remove_like(self, user_id, personality_id) -> bool:
        try:
            u_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            p_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return False

        result = self.collection.delete_one({"user_id": u_id, "personality_id": p_id, "type": "like"})
        return result.deleted_count > 0

    def has_liked(self, user_id, personality_id) -> bool:
        if not user_id or not personality_id:
            return False
        try:
            u_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            p_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return False

        return self.collection.find_one({"user_id": u_id, "personality_id": p_id, "type": "like"}) is not None

    def get_user_liked_personality_ids(self, user_id) -> set[str]:
        if not user_id:
            return set()
        try:
            u_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            return set()

        cursor = self.collection.find({"user_id": u_id, "type": "like"})
        return {str(doc["personality_id"]) for doc in cursor}
