from datetime import datetime, timezone
from bson import ObjectId


class Interaction:
    """
    Modelo de Interacciones (Likes, etc.).
    """
    TYPE_LIKE = "like"

    def __init__(
        self,
        user_id,
        personality_id,
        type="like",
        created_at=None,
        _id=None,
    ):
        self._id = ObjectId(_id) if _id and isinstance(_id, str) else _id or ObjectId()
        self.user_id = ObjectId(user_id) if user_id and isinstance(user_id, str) else user_id
        self.personality_id = ObjectId(personality_id) if personality_id and isinstance(personality_id, str) else personality_id
        self.type = type
        self.created_at = created_at or datetime.now(timezone.utc)

    @property
    def id(self):
        return str(self._id)

    def to_dict(self):
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "personality_id": self.personality_id,
            "type": self.type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            _id=data.get("_id"),
            user_id=data.get("user_id"),
            personality_id=data.get("personality_id"),
            type=data.get("type", "like"),
            created_at=data.get("created_at"),
        )
