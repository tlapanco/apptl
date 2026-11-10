import math
from app.repositories.personality_repository import PersonalityRepository
from app.repositories.user_repository import UserRepository
from app.repositories.interaction_repository import InteractionRepository


class CommunityService:
    """
    Servicio encargado de la comunidad, descubrimiento de personalidades públicas,
    búsqueda, filtros, ordenamiento y enriquecimiento con información de creadores.
    """
    def __init__(
        self,
        personality_repo: PersonalityRepository = None,
        user_repo: UserRepository = None,
        interaction_repo: InteractionRepository = None,
    ):
        self.personality_repo = personality_repo or PersonalityRepository()
        self.user_repo = user_repo or UserRepository()
        self.interaction_repo = interaction_repo or InteractionRepository()

    def get_public_feed(
        self,
        query: str = None,
        category: str = None,
        tag: str = None,
        sort_by: str = "popular",
        page: int = 1,
        per_page: int = 12,
        current_user_id = None,
    ) -> dict:
        """
        Búsqueda paginada y enriquecida para el explorador de la comunidad.
        """
        page = max(1, int(page)) if page else 1
        per_page = max(1, min(50, int(per_page))) if per_page else 12

        matching_owner_ids = []
        if query and query.strip():
            # Buscar usuarios cuyo username coincida con la consulta
            matching_users = self.user_repo.search_by_username(query.strip(), limit=20)
            matching_owner_ids = [u._id for u in matching_users]

        personalities, total_count = self.personality_repo.search_community(
            query=query,
            category=category,
            tag=tag,
            sort_by=sort_by,
            page=page,
            per_page=per_page,
            matching_owner_ids=matching_owner_ids,
        )

        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        liked_ids = set()
        if current_user_id:
            liked_ids = self.interaction_repo.get_user_liked_personality_ids(current_user_id)

        # Enriquecer con información del creador
        enriched_items = []
        for p in personalities:
            creator_name = "Sistema"
            creator_avatar = "🤖"
            creator_username = None

            if p.owner_id and not p.is_system:
                owner = self.user_repo.find_by_id(p.owner_id)
                if owner:
                    creator_name = owner.username
                    creator_avatar = owner.avatar or "👤"
                    creator_username = owner.username

            enriched_items.append({
                "personality": p,
                "creator_name": creator_name,
                "creator_avatar": creator_avatar,
                "creator_username": creator_username,
                "is_liked": str(p._id) in liked_ids,
            })

        return {
            "items": enriched_items,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "current_category": category or "all",
            "current_query": query or "",
            "current_tag": tag or "",
            "current_sort": sort_by or "popular",
        }
