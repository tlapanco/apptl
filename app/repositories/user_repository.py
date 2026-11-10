from bson import ObjectId
from datetime import datetime, timezone
from app.extensions.mongo import mongo
from app.models.user import User


class UserRepository:
    """
    Repositorio para gestionar operaciones de base de datos sobre la colección 'users'.
    """
    def __init__(self, db=None):
        self._db = db

    @property
    def collection(self):
        db = self._db or mongo.get_db()
        return db.users

    def create(self, user: User) -> User:
        user_dict = user.to_dict()
        self.collection.insert_one(user_dict)
        return user

    def find_by_id(self, user_id) -> User | None:
        if not user_id:
            return None
        try:
            obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            return None
        data = self.collection.find_one({"_id": obj_id})
        return User.from_dict(data) if data else None

    def find_by_email(self, email: str) -> User | None:
        if not email:
            return None
        data = self.collection.find_one({"email": email.strip().lower()})
        return User.from_dict(data) if data else None

    def find_by_username(self, username: str) -> User | None:
        if not username:
            return None
        data = self.collection.find_one({"username": username.strip()})
        return User.from_dict(data) if data else None

    def update(self, user: User) -> bool:
        user.updated_at = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"_id": user._id},
            {"$set": {
                "email": user.email,
                "username": user.username,
                "password_hash": user.password_hash,
                "avatar": user.avatar,
                "bio": user.bio,
                "updated_at": user.updated_at,
            }}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def search_by_username(self, query: str, limit: int = 10) -> list[User]:
        if not query:
            return []
        cursor = self.collection.find(
            {"username": {"$regex": query.strip(), "$options": "i"}}
        ).limit(limit)
        return [User.from_dict(doc) for doc in cursor]
