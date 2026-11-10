from bson import ObjectId
from app.models.personality import Personality
from app.repositories.personality_repository import PersonalityRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.user_repository import UserRepository
from app.services.friendship_service import FriendshipService


class PersonalityService:
    """
    Servicio de lógica de negocio para la gestión, autorización e interacción de Personalidades.
    """
    def __init__(
        self,
        personality_repo: PersonalityRepository = None,
        interaction_repo: InteractionRepository = None,
        user_repo: UserRepository = None,
        friendship_service: FriendshipService = None,
    ):
        self.personality_repo = personality_repo or PersonalityRepository()
        self.interaction_repo = interaction_repo or InteractionRepository()
        self.user_repo = user_repo or UserRepository()
        self.friendship_service = friendship_service or FriendshipService()

    def create_personality(
        self,
        user_id,
        name: str,
        description: str,
        system_prompt: str,
        avatar: str = None,
        visibility: str = "public",
        category: str = "Otros",
        tags: list[str] | str = None,
    ) -> tuple[Personality | None, str | None]:
        """Crea una nueva personalidad vinculada al usuario."""
        if not name or not name.strip():
            return None, "El nombre de la personalidad es obligatorio."
        if not description or not description.strip():
            return None, "La descripción es obligatoria."
        if not system_prompt or not system_prompt.strip():
            return None, "El prompt del sistema (instrucciones) es obligatorio."

        if visibility not in Personality.VALID_VISIBILITIES:
            visibility = "public"

        # Procesar tags si vienen como string delimitado por comas
        processed_tags = []
        if isinstance(tags, str):
            processed_tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif isinstance(tags, list):
            processed_tags = [str(t).strip() for t in tags if str(t).strip()]

        owner_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        personality = Personality(
            name=name.strip(),
            description=description.strip(),
            system_prompt=system_prompt.strip(),
            avatar=avatar.strip() if avatar else "🤖",
            owner_id=owner_oid,
            is_system=False,
            visibility=visibility,
            category=category or "Otros",
            tags=processed_tags,
        )

        created = self.personality_repo.create(personality)
        return created, None

    def update_personality(
        self,
        user_id,
        personality_id,
        name: str,
        description: str,
        system_prompt: str,
        avatar: str = None,
        visibility: str = "public",
        category: str = "Otros",
        tags: list[str] | str = None,
        change_notes: str = None,
    ) -> tuple[Personality | None, str | None]:
        """Actualiza una personalidad existente, registrando un nuevo punto de versión en su historial."""
        personality = self.personality_repo.find_by_id(personality_id)
        if not personality:
            return None, "Personalidad no encontrada."

        if not self.can_user_edit_personality(user_id, personality):
            return None, "No tienes permiso para modificar esta personalidad."

        if not name or not name.strip():
            return None, "El nombre no puede estar vacío."
        if not description or not description.strip():
            return None, "La descripción no puede estar vacía."
        if not system_prompt or not system_prompt.strip():
            return None, "El prompt del sistema no puede estar vacío."

        if visibility not in Personality.VALID_VISIBILITIES:
            visibility = "public"

        processed_tags = []
        if isinstance(tags, str):
            processed_tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif isinstance(tags, list):
            processed_tags = [str(t).strip() for t in tags if str(t).strip()]

        final_avatar = avatar.strip() if avatar else personality.avatar

        # Registrar nueva versión en el historial de la personalidad
        personality.record_new_version(
            name=name.strip(),
            description=description.strip(),
            system_prompt=system_prompt.strip(),
            avatar=final_avatar,
            category=category or "Otros",
            tags=processed_tags,
            visibility=visibility,
            change_notes=change_notes,
        )

        self.personality_repo.update(personality)
        return personality, None

    def delete_personality(self, user_id, personality_id) -> tuple[bool, str | None]:
        """Elimina una personalidad verificando propiedad."""
        personality = self.personality_repo.find_by_id(personality_id)
        if not personality:
            return False, "Personalidad no encontrada."

        if not self.can_user_edit_personality(user_id, personality):
            return False, "No tienes permiso para eliminar esta personalidad."

        success = self.personality_repo.delete(personality._id)
        return success, None

    def get_personality(self, personality_id) -> Personality | None:
        return self.personality_repo.find_by_id(personality_id)

    def can_user_access_personality(self, user_id, personality: Personality) -> bool:
        """
        Reglas de autorización para usar o ver una personalidad:
        1. Es del sistema -> Sí
        2. Es pública -> Sí
        3. El usuario es el creador/propietario -> Sí
        4. Es para amigos (friends) -> Sí, si el usuario y el creador son amigos aceptados
        """
        if not personality:
            return False

        if personality.is_system:
            return True

        if not user_id:
            return personality.visibility == "public"

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        if personality.owner_id == u_oid:
            return True

        if personality.visibility == "public":
            return True

        if personality.visibility == "friends" and personality.owner_id:
            return self.friendship_service.are_friends(u_oid, personality.owner_id)

        return False

    def can_user_edit_personality(self, user_id, personality: Personality) -> bool:
        """Solo el propietario puede editar o eliminar su personalidad (las del sistema no son editables por usuarios)."""
        if not personality or personality.is_system or not user_id:
            return False
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        return personality.owner_id == u_oid

    def toggle_like(self, user_id, personality_id) -> tuple[bool, int, str | None]:
        """
        Alterna el like de un usuario en una personalidad.
        Retorna (ha_dado_like, nuevo_total_likes, mensaje_error).
        """
        if not user_id:
            return False, 0, "Debes iniciar sesión para dar like."

        personality = self.personality_repo.find_by_id(personality_id)
        if not personality:
            return False, 0, "Personalidad no encontrada."

        # Solo se permite dar like a personalidades públicas o accesibles
        if not self.can_user_access_personality(user_id, personality):
            return False, personality.likes_count, "No tienes permiso para interactuar con esta personalidad."

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        already_liked = self.interaction_repo.has_liked(u_oid, personality._id)

        if already_liked:
            self.interaction_repo.remove_like(u_oid, personality._id)
            self.personality_repo.update_likes_count(personality._id, -1)
            new_count = max(0, personality.likes_count - 1)
            return False, new_count, None
        else:
            self.interaction_repo.add_like(u_oid, personality._id)
            self.personality_repo.update_likes_count(personality._id, 1)
            new_count = personality.likes_count + 1
            return True, new_count, None

    def get_user_personalities(self, user_id) -> list[Personality]:
        return self.personality_repo.find_by_owner_id(user_id)

    def get_system_personalities(self) -> list[Personality]:
        return self.personality_repo.find_system_personalities()

    def get_user_liked_ids(self, user_id) -> set[str]:
        return self.interaction_repo.get_user_liked_personality_ids(user_id)
