from bson import ObjectId
from datetime import datetime, timezone
from app.models.chat import Chat
from app.repositories.chat_repository import ChatRepository
from app.repositories.personality_repository import PersonalityRepository
from app.services.personality_service import PersonalityService
from app.services.ai_service import AIService


class ChatService:
    """
    Servicio encargado del ciclo de vida de conversaciones, mensajes y su orquestación con AIService.
    """
    def __init__(
        self,
        chat_repo: ChatRepository = None,
        personality_repo: PersonalityRepository = None,
        personality_service: PersonalityService = None,
        ai_service: AIService = None,
    ):
        self.chat_repo = chat_repo or ChatRepository()
        self.personality_repo = personality_repo or PersonalityRepository()
        self.personality_service = personality_service or PersonalityService(self.personality_repo)
        self.ai_service = ai_service or AIService()

    def create_chat(self, user_id, personality_id, version_number: int = None) -> tuple[Chat | None, str | None]:
        """
        Crea un nuevo chat asociado a una personalidad, guardando el snapshot de la versión seleccionada.
        """
        personality = self.personality_service.get_personality(personality_id)
        if not personality:
            return None, "Personalidad no encontrada."

        if not self.personality_service.can_user_access_personality(user_id, personality):
            return None, "No tienes permiso para utilizar esta personalidad."

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        # Obtener snapshot de la versión específica o la más reciente
        v_snapshot = None
        if version_number:
            v_snapshot = personality.get_version(version_number)
        
        if not v_snapshot:
            v_snapshot = personality.get_latest_version_snapshot()

        selected_version_num = v_snapshot.get("version_number", personality.current_version)

        snapshot = {
            "name": v_snapshot.get("name", personality.name),
            "system_prompt": v_snapshot.get("system_prompt", personality.system_prompt),
            "avatar": v_snapshot.get("avatar", personality.avatar),
            "description": v_snapshot.get("description", personality.description),
            "category": v_snapshot.get("category", personality.category),
            "version_number": selected_version_num,
            "version_label": v_snapshot.get("version_label", f"v{selected_version_num}.0"),
        }

        # Incrementar contador de usos en backend
        self.personality_repo.increment_uses_count(personality._id)

        chat = Chat(
            user_id=u_oid,
            personality_id=personality._id,
            personality_snapshot=snapshot,
            personality_version=selected_version_num,
            title=f"Chat con {snapshot['name']}",
            messages=[]
        )

        created_chat = self.chat_repo.create(chat)
        return created_chat, None

    def sync_personality(self, user_id, chat_id, target_version: int = None) -> tuple[Chat | None, str | None]:
        """
        Actualiza el snapshot y avatar del chat a la versión más reciente o a una versión específica de la personalidad.
        """
        chat, error = self.get_chat(user_id, chat_id)
        if error or not chat:
            return None, error or "Conversación no encontrada."

        if not chat.personality_id:
            return None, "Este chat no tiene una personalidad vinculada."

        personality = self.personality_service.get_personality(chat.personality_id)
        if not personality:
            return None, "La personalidad vinculada ya no existe en el sistema."

        if target_version:
            v_data = personality.get_version(target_version)
            if not v_data:
                return None, f"La versión {target_version} no fue encontrada."
        else:
            v_data = personality.get_latest_version_snapshot()

        ver_num = v_data.get("version_number", personality.current_version)
        new_snapshot = {
            "name": v_data.get("name", personality.name),
            "system_prompt": v_data.get("system_prompt", personality.system_prompt),
            "avatar": v_data.get("avatar", personality.avatar),
            "description": v_data.get("description", personality.description),
            "category": v_data.get("category", personality.category),
            "version_number": ver_num,
            "version_label": v_data.get("version_label", f"v{ver_num}.0"),
        }

        chat.update_personality_snapshot(new_snapshot, version_number=ver_num)
        self.chat_repo.update_snapshot(chat._id, new_snapshot, version_number=ver_num)

        return chat, None

    def get_chat(self, user_id, chat_id) -> tuple[Chat | None, str | None]:
        """Obtiene un chat verificando que pertenezca al usuario."""
        chat = self.chat_repo.find_by_id(chat_id)
        if not chat:
            return None, "Conversación no encontrada."

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        if chat.user_id != u_oid:
            return None, "No tienes acceso a esta conversación."

        return chat, None

    def get_user_chats(self, user_id, limit: int = 50, skip: int = 0) -> list[Chat]:
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        return self.chat_repo.find_by_user_id(u_oid, limit=limit, skip=skip)

    def send_message(self, user_id, chat_id, content: str) -> tuple[dict | None, str | None]:
        """
        Flujo de mensaje:
        1. Verificar propietario.
        2. Validar contenido.
        3. Guardar mensaje de usuario.
        4. Invocar AIService con system_prompt y mensajes.
        5. Guardar respuesta de IA.
        6. Actualizar título si es el primer mensaje.
        7. Retornar mensaje de IA.
        """
        chat, error = self.get_chat(user_id, chat_id)
        if error or not chat:
            return None, error or "Chat no encontrado."

        if not content or not content.strip():
            return None, "El mensaje no puede estar vacío."

        clean_content = content.strip()

        # Mensaje de usuario
        user_msg = {
            "role": "user",
            "content": clean_content,
            "created_at": datetime.now(timezone.utc),
        }

        # Determinar si actualizar el título (si es el primer mensaje o título por defecto)
        new_title = None
        if len(chat.messages) == 0 or chat.title.startswith("Chat con") or chat.title == "Nuevo chat":
            # Título conciso del primer mensaje
            snippet = clean_content[:35].strip()
            if len(clean_content) > 35:
                snippet += "..."
            new_title = snippet

        # Guardar mensaje de usuario primero
        self.chat_repo.add_message(chat._id, user_msg, new_title=new_title)

        # Preparar historial completo para la IA
        conversation_history = list(chat.messages) + [user_msg]
        system_prompt = chat.personality_snapshot.get(
            "system_prompt",
            f"Eres {chat.personality_snapshot.get('name', 'un asistente')}. Responde de forma útil y coherente."
        )

        # Llamar a AIService (Gemini)
        ai_reply_text, success, ai_error = self.ai_service.generate_response(
            system_prompt=system_prompt,
            messages=conversation_history
        )

        # Guardar respuesta del asistente
        ai_msg = {
            "role": "assistant",
            "content": ai_reply_text,
            "created_at": datetime.now(timezone.utc),
        }
        self.chat_repo.add_message(chat._id, ai_msg)

        return ai_msg, None

    def delete_chat(self, user_id, chat_id) -> tuple[bool, str | None]:
        """Elimina un chat verificando propiedad."""
        chat, error = self.get_chat(user_id, chat_id)
        if error or not chat:
            return False, error or "Chat no encontrado."

        success = self.chat_repo.delete(chat._id)
        return success, None
