from .auth import auth_bp
from .chats import chats_bp
from .personalities import personalities_bp
from .community import community_bp
from .users import users_bp
from .friendships import friendships_bp
from .dashboard import dashboard_bp

__all__ = [
    "auth_bp",
    "chats_bp",
    "personalities_bp",
    "community_bp",
    "users_bp",
    "friendships_bp",
    "dashboard_bp",
]
