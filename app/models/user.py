from datetime import datetime, timezone
from bson import ObjectId
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    """
    Modelo de Usuario compatible con Flask-Login y MongoDB.
    """
    def __init__(
        self,
        email,
        username,
        password_hash=None,
        avatar=None,
        bio="",
        created_at=None,
        updated_at=None,
        _id=None,
    ):
        self._id = ObjectId(_id) if _id and isinstance(_id, str) else _id or ObjectId()
        self.email = email.strip().lower() if email else ""
        self.username = username.strip() if username else ""
        self.password_hash = password_hash
        self.avatar = avatar or ""
        self.bio = bio or ""
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @property
    def id(self):
        return str(self._id)

    def get_id(self):
        return str(self._id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "_id": self._id,
            "email": self.email,
            "username": self.username,
            "password_hash": self.password_hash,
            "avatar": self.avatar,
            "bio": self.bio,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            _id=data.get("_id"),
            email=data.get("email"),
            username=data.get("username"),
            password_hash=data.get("password_hash"),
            avatar=data.get("avatar"),
            bio=data.get("bio", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
