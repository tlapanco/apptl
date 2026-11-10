from datetime import datetime, timezone
from bson import ObjectId


class Friendship:
    """
    Modelo de Relación de Amistad entre dos usuarios.
    Estados: 'pending', 'accepted', 'rejected'
    """
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    def __init__(
        self,
        requester_id,
        receiver_id,
        status="pending",
        created_at=None,
        updated_at=None,
        _id=None,
    ):
        self._id = ObjectId(_id) if _id and isinstance(_id, str) else _id or ObjectId()
        self.requester_id = ObjectId(requester_id) if requester_id and isinstance(requester_id, str) else requester_id
        self.receiver_id = ObjectId(receiver_id) if receiver_id and isinstance(receiver_id, str) else receiver_id
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @property
    def id(self):
        return str(self._id)

    def to_dict(self):
        return {
            "_id": self._id,
            "requester_id": self.requester_id,
            "receiver_id": self.receiver_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            _id=data.get("_id"),
            requester_id=data.get("requester_id"),
            receiver_id=data.get("receiver_id"),
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
