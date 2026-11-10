from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services.personality_service import PersonalityService
from app.services.chat_service import ChatService
from app.services.friendship_service import FriendshipService

dashboard_bp = Blueprint("dashboard", __name__)
personality_service = PersonalityService()
chat_service = ChatService()
friendship_service = FriendshipService()


@dashboard_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def index():
    recent_chats = chat_service.get_user_chats(current_user._id, limit=6)
    system_personalities = personality_service.get_system_personalities()
    my_personalities = personality_service.get_user_personalities(current_user._id)
    liked_ids = personality_service.get_user_liked_ids(current_user._id)
    friendships_data = friendship_service.get_user_friendships_detailed(current_user._id)

    return render_template(
        "dashboard/index.html",
        recent_chats=recent_chats,
        system_personalities=system_personalities,
        my_personalities=my_personalities,
        liked_ids=liked_ids,
        friends_count=len(friendships_data.get("friends", [])),
        pending_requests_count=len(friendships_data.get("pending_received", [])),
    )
