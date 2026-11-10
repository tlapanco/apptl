from datetime import datetime, timezone
from bson import ObjectId


class Personality:
    """
    Modelo de Personalidad de IA.
    """
    VALID_VISIBILITIES = ["private", "friends", "public"]
    DEFAULT_CATEGORIES = [
        "Programación",
        "Educación",
        "Escritura",
        "Productividad",
        "Entretenimiento",
        "Creatividad",
        "Negocios",
        "Idiomas",
        "Otros",
    ]

    def __init__(
        self,
        name,
        description,
        system_prompt,
        avatar=None,
        owner_id=None,
        is_system=False,
        visibility="public",
        category="Otros",
        tags=None,
        likes_count=0,
        uses_count=0,
        current_version=1,
        versions=None,
        created_at=None,
        updated_at=None,
        _id=None,
    ):
        self._id = ObjectId(_id) if _id and isinstance(_id, str) else _id or ObjectId()
        self.name = name.strip() if name else ""
        self.description = description.strip() if description else ""
        self.system_prompt = system_prompt.strip() if system_prompt else ""
        self.avatar = avatar or "🤖"
        self.owner_id = ObjectId(owner_id) if owner_id and isinstance(owner_id, str) else owner_id
        self.is_system = bool(is_system)
        self.visibility = visibility if visibility in self.VALID_VISIBILITIES else "public"
        self.category = category or "Otros"
        
        # Normalizar tags (sin duplicados, minúsculas o capitalizados limpiamente)
        clean_tags = []
        if tags:
            for t in tags:
                if isinstance(t, str) and t.strip():
                    val = t.strip()
                    if val not in clean_tags:
                        clean_tags.append(val)
        self.tags = clean_tags

        self.likes_count = int(likes_count) if likes_count else 0
        self.uses_count = int(uses_count) if uses_count else 0
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

        # Versionado de la personalidad
        self.current_version = int(current_version) if current_version else 1
        
        # Inicializar historial de versiones
        if versions and isinstance(versions, list) and len(versions) > 0:
            self.versions = versions
        else:
            self.versions = [{
                "version_number": 1,
                "version_label": "v1.0",
                "name": self.name,
                "description": self.description,
                "system_prompt": self.system_prompt,
                "avatar": self.avatar,
                "category": self.category,
                "tags": self.tags,
                "visibility": self.visibility,
                "change_notes": "Versión inicial",
                "created_at": self.created_at,
            }]

    def get_version(self, version_number: int) -> dict | None:
        """Obtiene los datos de una versión específica."""
        try:
            target_v = int(version_number)
            for v in self.versions:
                if int(v.get("version_number", 0)) == target_v:
                    return v
        except Exception:
            pass
        return None

    def get_latest_version_snapshot(self) -> dict:
        """Retorna el snapshot de la versión activa/más reciente."""
        if self.versions:
            # Buscar la versión que coincida con current_version o la última
            for v in self.versions:
                if int(v.get("version_number", 0)) == self.current_version:
                    return v
            return self.versions[-1]
        return {
            "version_number": self.current_version,
            "version_label": f"v{self.current_version}.0",
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "avatar": self.avatar,
            "category": self.category,
            "tags": self.tags,
            "visibility": self.visibility,
            "change_notes": "Versión activa",
            "created_at": self.updated_at,
        }

    def record_new_version(
        self,
        name: str,
        description: str,
        system_prompt: str,
        avatar: str,
        category: str,
        tags: list,
        visibility: str,
        change_notes: str = None
    ) -> int:
        """
        Registra una nueva versión si hay cambios significativos y actualiza los campos activos.
        """
        new_v_number = len(self.versions) + 1 if self.versions else self.current_version + 1
        now = datetime.now(timezone.utc)
        
        notes = change_notes.strip() if change_notes and change_notes.strip() else f"Actualización a v{new_v_number}"
        
        version_entry = {
            "version_number": new_v_number,
            "version_label": f"v{new_v_number}.0",
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "avatar": avatar,
            "category": category,
            "tags": tags,
            "visibility": visibility,
            "change_notes": notes,
            "created_at": now,
        }
        
        self.versions.append(version_entry)
        self.current_version = new_v_number
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.avatar = avatar
        self.category = category
        self.tags = tags
        self.visibility = visibility
        self.updated_at = now
        
        return new_v_number

    @property
    def id(self):
        return str(self._id)

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "avatar": self.avatar,
            "owner_id": self.owner_id,
            "is_system": self.is_system,
            "visibility": self.visibility,
            "category": self.category,
            "tags": self.tags,
            "likes_count": self.likes_count,
            "uses_count": self.uses_count,
            "current_version": self.current_version,
            "versions": self.versions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            _id=data.get("_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            avatar=data.get("avatar"),
            owner_id=data.get("owner_id"),
            is_system=data.get("is_system", False),
            visibility=data.get("visibility", "public"),
            category=data.get("category", "Otros"),
            tags=data.get("tags", []),
            likes_count=data.get("likes_count", 0),
            uses_count=data.get("uses_count", 0),
            current_version=data.get("current_version", 1),
            versions=data.get("versions", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
