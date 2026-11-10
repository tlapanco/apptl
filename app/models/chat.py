from datetime import datetime, timezone
from bson import ObjectId


class Chat:
    """
    Modelo de Conversación / Chat.
    Almacena el personality_snapshot y personality_version para trazabilidad y versionado.
    """
    def __init__(
        self,
        user_id,
        personality_id,
        personality_snapshot,
        personality_version=1,
        title="Nuevo chat",
        messages=None,
        created_at=None,
        updated_at=None,
        _id=None,
    ):
        self._id = ObjectId(_id) if _id and isinstance(_id, str) else _id or ObjectId()
        self.user_id = ObjectId(user_id) if user_id and isinstance(user_id, str) else user_id
        self.personality_id = ObjectId(personality_id) if personality_id and isinstance(personality_id, str) else personality_id
        self.personality_snapshot = personality_snapshot or {}
        
        # Versión de la personalidad vinculada
        if personality_version:
            self.personality_version = int(personality_version)
        else:
            self.personality_version = int(self.personality_snapshot.get("version_number", 1))

        self.title = title or "Nuevo chat"
        self.messages = messages or []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @property
    def id(self):
        return str(self._id)

    def add_message(self, role, content):
        msg = {
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
        self.messages.append(msg)
        self.updated_at = datetime.now(timezone.utc)
        return msg

    def update_personality_snapshot(self, snapshot: dict, version_number: int = None):
        """Actualiza el snapshot y la versión activa de la personalidad en este chat."""
        if snapshot:
            self.personality_snapshot = {
                "name": snapshot.get("name", self.personality_snapshot.get("name", "Asistente")),
                "system_prompt": snapshot.get("system_prompt", self.personality_snapshot.get("system_prompt", "")),
                "avatar": snapshot.get("avatar", self.personality_snapshot.get("avatar", "🤖")),
                "description": snapshot.get("description", self.personality_snapshot.get("description", "")),
                "category": snapshot.get("category", self.personality_snapshot.get("category", "Otros")),
                "version_number": snapshot.get("version_number", version_number or self.personality_version),
                "version_label": snapshot.get("version_label", f"v{version_number or self.personality_version}.0"),
            }
            if version_number:
                self.personality_version = int(version_number)
            elif snapshot.get("version_number"):
                self.personality_version = int(snapshot.get("version_number"))
            self.updated_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "personality_id": self.personality_id,
            "personality_version": self.personality_version,
            "personality_snapshot": {
                "name": self.personality_snapshot.get("name", "Asistente"),
                "system_prompt": self.personality_snapshot.get("system_prompt", ""),
                "avatar": self.personality_snapshot.get("avatar", "🤖"),
                "description": self.personality_snapshot.get("description", ""),
                "category": self.personality_snapshot.get("category", "Otros"),
                "version_number": self.personality_snapshot.get("version_number", self.personality_version),
                "version_label": self.personality_snapshot.get("version_label", f"v{self.personality_version}.0"),
            },
            "title": self.title,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        snapshot = data.get("personality_snapshot", {})
        version = data.get("personality_version") or snapshot.get("version_number", 1)
        return cls(
            _id=data.get("_id"),
            user_id=data.get("user_id"),
            personality_id=data.get("personality_id"),
            personality_version=version,
            personality_snapshot=snapshot,
            title=data.get("title", "Nuevo chat"),
            messages=data.get("messages", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
