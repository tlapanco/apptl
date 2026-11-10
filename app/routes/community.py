from flask import Blueprint, render_template, request
from flask_login import current_user
from app.services.community_service import CommunityService
from app.models.personality import Personality

community_bp = Blueprint("community", __name__, url_prefix="/community")
community_service = CommunityService()


@community_bp.route("", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "all").strip()
    tag = request.args.get("tag", "").strip()
    sort_by = request.args.get("sort", "popular").strip()
    page = request.args.get("page", 1, type=int)

    current_user_id = current_user._id if current_user.is_authenticated else None

    feed = community_service.get_public_feed(
        query=query,
        category=category,
        tag=tag,
        sort_by=sort_by,
        page=page,
        per_page=12,
        current_user_id=current_user_id,
    )

    return render_template(
        "community/index.html",
        feed=feed,
        categories=Personality.DEFAULT_CATEGORIES,
    )
