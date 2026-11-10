from bson import ObjectId
from datetime import datetime, timezone
from pymongo import DESCENDING, ASCENDING
from app.extensions.mongo import mongo
from app.models.personality import Personality


class PersonalityRepository:
    """
    Repositorio para gestionar operaciones de base de datos sobre la colección 'personalities'.
    """
    def __init__(self, db=None):
        self._db = db

    @property
    def collection(self):
        db = self._db or mongo.get_db()
        return db.personalities

    def create(self, personality: Personality) -> Personality:
        data = personality.to_dict()
        self.collection.insert_one(data)
        return personality

    def find_by_id(self, personality_id) -> Personality | None:
        if not personality_id:
            return None
        try:
            obj_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return None
        data = self.collection.find_one({"_id": obj_id})
        return Personality.from_dict(data) if data else None

    def find_by_name(self, name: str) -> Personality | None:
        if not name:
            return None
        data = self.collection.find_one({"name": name.strip()})
        return Personality.from_dict(data) if data else None

    def find_by_owner_id(self, owner_id) -> list[Personality]:
        if not owner_id:
            return []
        try:
            obj_id = ObjectId(owner_id) if isinstance(owner_id, str) else owner_id
        except Exception:
            return []
        cursor = self.collection.find({"owner_id": obj_id}).sort("updated_at", DESCENDING)
        return [Personality.from_dict(doc) for doc in cursor]

    def find_system_personalities(self) -> list[Personality]:
        cursor = self.collection.find({"is_system": True}).sort("name", ASCENDING)
        return [Personality.from_dict(doc) for doc in cursor]

    def update(self, personality: Personality) -> bool:
        personality.updated_at = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"_id": personality._id},
            {"$set": {
                "name": personality.name,
                "description": personality.description,
                "system_prompt": personality.system_prompt,
                "avatar": personality.avatar,
                "visibility": personality.visibility,
                "category": personality.category,
                "tags": personality.tags,
                "current_version": personality.current_version,
                "versions": personality.versions,
                "updated_at": personality.updated_at,
            }}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def delete(self, personality_id) -> bool:
        try:
            obj_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return False
        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0

    def increment_uses_count(self, personality_id) -> bool:
        try:
            obj_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return False
        result = self.collection.update_one(
            {"_id": obj_id},
            {"$inc": {"uses_count": 1}}
        )
        return result.modified_count > 0

    def update_likes_count(self, personality_id, delta: int) -> bool:
        try:
            obj_id = ObjectId(personality_id) if isinstance(personality_id, str) else personality_id
        except Exception:
            return False
        result = self.collection.update_one(
            {"_id": obj_id},
            {"$inc": {"likes_count": delta}}
        )
        return result.modified_count > 0

    def search_community(
        self,
        query: str = None,
        category: str = None,
        tag: str = None,
        sort_by: str = "popular",
        page: int = 1,
        per_page: int = 12,
        matching_owner_ids: list = None,
    ) -> tuple[list[Personality], int]:
        """
        Búsqueda paginada en la comunidad para personalidades públicas.
        Permite filtrar por texto (nombre, descripción, tags, creador), categoría, tag y ordenar.
        """
        filter_query = {"visibility": "public"}

        # Filtro de categoría
        if category and category != "all":
            filter_query["category"] = category

        # Filtro de tag
        if tag:
            filter_query["tags"] = {"$in": [tag]}

        # Filtro de texto
        if query:
            q_clean = query.strip()
            text_conditions = [
                {"name": {"$regex": q_clean, "$options": "i"}},
                {"description": {"$regex": q_clean, "$options": "i"}},
                {"tags": {"$in": [q_clean]}},
            ]
            if matching_owner_ids:
                text_conditions.append({"owner_id": {"$in": matching_owner_ids}})
            filter_query["$or"] = text_conditions

        # Ordenamiento
        sort_field = "likes_count"
        sort_dir = DESCENDING

        if sort_by == "recent":
            sort_field = "created_at"
            sort_dir = DESCENDING
        elif sort_by == "uses":
            sort_field = "uses_count"
            sort_dir = DESCENDING
        elif sort_by == "name":
            sort_field = "name"
            sort_dir = ASCENDING
        else: # "popular"
            sort_field = "likes_count"
            sort_dir = DESCENDING

        total_count = self.collection.count_documents(filter_query)
        skip = (page - 1) * per_page

        cursor = self.collection.find(filter_query).sort(sort_field, sort_dir).skip(skip).limit(per_page)
        items = [Personality.from_dict(doc) for doc in cursor]

        return items, total_count
