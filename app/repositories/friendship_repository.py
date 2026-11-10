from bson import ObjectId
from datetime import datetime, timezone
from pymongo import DESCENDING
from app.extensions.mongo import mongo
from app.models.friendship import Friendship


class FriendshipRepository:
    """
    Repositorio para gestionar solicitudes y relaciones de amistad entre usuarios.
    """
    def __init__(self, db=None):
        self._db = db

    @property
    def collection(self):
        db = self._db or mongo.get_db()
        return db.friendships

    def create(self, friendship: Friendship) -> Friendship:
        data = friendship.to_dict()
        self.collection.insert_one(data)
        return friendship

    def find_by_id(self, friendship_id) -> Friendship | None:
        if not friendship_id:
            return None
        try:
            obj_id = ObjectId(friendship_id) if isinstance(friendship_id, str) else friendship_id
        except Exception:
            return None
        data = self.collection.find_one({"_id": obj_id})
        return Friendship.from_dict(data) if data else None

    def find_between(self, user_a_id, user_b_id) -> Friendship | None:
        """Buscar cualquier relación (en cualquier dirección) entre dos usuarios."""
        try:
            a_id = ObjectId(user_a_id) if isinstance(user_a_id, str) else user_a_id
            b_id = ObjectId(user_b_id) if isinstance(user_b_id, str) else user_b_id
        except Exception:
            return None
        
        data = self.collection.find_one({
            "$or": [
                {"requester_id": a_id, "receiver_id": b_id},
                {"requester_id": b_id, "receiver_id": a_id}
            ]
        })
        return Friendship.from_dict(data) if data else None

    def find_all_for_user(self, user_id, status: str = None) -> list[Friendship]:
        try:
            obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            return []

        query = {"$or": [{"requester_id": obj_id}, {"receiver_id": obj_id}]}
        if status:
            query["status"] = status

        cursor = self.collection.find(query).sort("updated_at", DESCENDING)
        return [Friendship.from_dict(doc) for doc in cursor]

    def find_accepted_friend_ids(self, user_id) -> list[ObjectId]:
        """Obtiene la lista de ObjectId de los amigos aceptados de un usuario."""
        try:
            obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            return []

        cursor = self.collection.find({
            "$or": [{"requester_id": obj_id}, {"receiver_id": obj_id}],
            "status": "accepted"
        })

        friend_ids = []
        for doc in cursor:
            if doc["requester_id"] == obj_id:
                friend_ids.append(doc["receiver_id"])
            else:
                friend_ids.append(doc["requester_id"])
        return friend_ids

    def update_status(self, friendship_id, status: str) -> bool:
        try:
            obj_id = ObjectId(friendship_id) if isinstance(friendship_id, str) else friendship_id
        except Exception:
            return False
        
        now = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"_id": obj_id},
            {"$set": {"status": status, "updated_at": now}}
        )
        return result.modified_count > 0

    def delete(self, friendship_id) -> bool:
        try:
            obj_id = ObjectId(friendship_id) if isinstance(friendship_id, str) else friendship_id
        except Exception:
            return False
        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0
