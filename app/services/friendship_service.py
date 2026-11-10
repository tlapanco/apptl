from bson import ObjectId
from app.models.friendship import Friendship
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository


class FriendshipService:
    """
    Servicio para gestionar la lógica de amistades entre usuarios.
    """
    def __init__(self, friendship_repo: FriendshipRepository = None, user_repo: UserRepository = None):
        self.friendship_repo = friendship_repo or FriendshipRepository()
        self.user_repo = user_repo or UserRepository()

    def send_request(self, requester_id, receiver_username: str) -> tuple[Friendship | None, str | None]:
        """Envía una solicitud de amistad por nombre de usuario."""
        if not receiver_username or not receiver_username.strip():
            return None, "Debes especificar el nombre del usuario."

        receiver = self.user_repo.find_by_username(receiver_username.strip())
        if not receiver:
            return None, f"No se encontró al usuario '{receiver_username}'."

        req_oid = ObjectId(requester_id) if isinstance(requester_id, str) else requester_id
        if receiver._id == req_oid:
            return None, "No puedes enviarte una solicitud de amistad a ti mismo."

        existing = self.friendship_repo.find_between(req_oid, receiver._id)
        if existing:
            if existing.status == "accepted":
                return None, "Ya son amigos."
            elif existing.status == "pending":
                if existing.requester_id == req_oid:
                    return None, "Ya enviaste una solicitud pendiente a este usuario."
                else:
                    # El otro usuario ya le envió una solicitud, aceptarla automáticamente
                    self.friendship_repo.update_status(existing._id, "accepted")
                    return existing, "¡Solicitud mutua aceptada! Ahora son amigos."
            elif existing.status == "rejected":
                # Si fue rechazada anteriormente, reactivarla
                self.friendship_repo.update_status(existing._id, "pending")
                return existing, None

        friendship = Friendship(
            requester_id=req_oid,
            receiver_id=receiver._id,
            status="pending"
        )
        created = self.friendship_repo.create(friendship)
        return created, None

    def accept_request(self, user_id, friendship_id) -> tuple[bool, str | None]:
        """Acepta una solicitud de amistad dirigida al usuario actual."""
        friendship = self.friendship_repo.find_by_id(friendship_id)
        if not friendship:
            return False, "Solicitud no encontrada."

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        if friendship.receiver_id != u_oid:
            return False, "No tienes permiso para responder a esta solicitud."

        if friendship.status == "accepted":
            return True, "Ya son amigos."

        self.friendship_repo.update_status(friendship._id, "accepted")
        return True, None

    def reject_request(self, user_id, friendship_id) -> tuple[bool, str | None]:
        """Rechaza una solicitud de amistad."""
        friendship = self.friendship_repo.find_by_id(friendship_id)
        if not friendship:
            return False, "Solicitud no encontrada."

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        if friendship.receiver_id != u_oid and friendship.requester_id != u_oid:
            return False, "No tienes permiso para modificar esta relación."

        self.friendship_repo.delete(friendship._id)
        return True, None

    def remove_friendship(self, user_id, target_user_id) -> tuple[bool, str | None]:
        """Elimina una relación de amistad existente."""
        friendship = self.friendship_repo.find_between(user_id, target_user_id)
        if not friendship:
            return False, "No existe una relación de amistad con este usuario."

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        if friendship.requester_id != u_oid and friendship.receiver_id != u_oid:
            return False, "No autorizado."

        self.friendship_repo.delete(friendship._id)
        return True, None

    def are_friends(self, user_a_id, user_b_id) -> bool:
        """Comprueba si dos usuarios son amigos aceptados."""
        if not user_a_id or not user_b_id:
            return False
        if str(user_a_id) == str(user_b_id):
            return True
        friendship = self.friendship_repo.find_between(user_a_id, user_b_id)
        return friendship is not None and friendship.status == "accepted"

    def get_user_friendships_detailed(self, user_id) -> dict:
        """
        Obtiene amigos aceptados, solicitudes recibidas pendientes y enviadas pendientes
        con detalles del usuario para visualización en interfaz.
        """
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        all_rels = self.friendship_repo.find_all_for_user(u_oid)

        accepted_friends = []
        pending_received = []
        pending_sent = []

        for rel in all_rels:
            is_requester = rel.requester_id == u_oid
            other_user_id = rel.receiver_id if is_requester else rel.requester_id
            other_user = self.user_repo.find_by_id(other_user_id)

            if not other_user:
                continue

            item = {
                "friendship_id": rel.id,
                "user": other_user,
                "status": rel.status,
                "created_at": rel.created_at,
            }

            if rel.status == "accepted":
                accepted_friends.append(item)
            elif rel.status == "pending":
                if is_requester:
                    pending_sent.append(item)
                else:
                    pending_received.append(item)

        return {
            "friends": accepted_friends,
            "pending_received": pending_received,
            "pending_sent": pending_sent,
        }
