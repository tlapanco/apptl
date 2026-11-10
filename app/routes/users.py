from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.auth_service import AuthService
from app.services.personality_service import PersonalityService
from app.services.friendship_service import FriendshipService
from app.utils.avatar_helper import save_avatar_file

users_bp = Blueprint("users", __name__, url_prefix="/users")
auth_service = AuthService()
personality_service = PersonalityService()
friendship_service = FriendshipService()


@users_bp.route("/<username>", methods=["GET"])
def profile(username):
    user = auth_service.get_user_by_username(username)
    if not user:
        flash("Usuario no encontrado.", "warning")
        return redirect(url_for("community.index")), 404

    # Obtener personalidades públicas creadas por este usuario
    user_personalities = personality_service.get_user_personalities(user._id)
    
    # Filtrar solo las que el visitante tiene derecho a ver
    visible_personalities = []
    current_uid = current_user._id if current_user.is_authenticated else None
    for p in user_personalities:
        if personality_service.can_user_access_personality(current_uid, p):
            visible_personalities.append(p)

    # Estado de amistad
    are_friends = False
    is_self = False
    if current_user.is_authenticated:
        is_self = str(current_user._id) == str(user._id)
        are_friends = friendship_service.are_friends(current_user._id, user._id)

    return render_template(
        "users/profile.html",
        user=user,
        personalities=visible_personalities,
        is_self=is_self,
        are_friends=are_friends,
    )


@users_bp.route("/me/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        bio = request.form.get("bio", "").strip()
        avatar_type = request.form.get("avatar_type", "emoji")
        avatar = current_user.avatar or "👤"

        if "avatar_file" in request.files and request.files["avatar_file"].filename:
            saved_url, err = save_avatar_file(request.files["avatar_file"])
            if err:
                flash(err, "danger")
                return render_template("users/edit.html", user=current_user), 400
            avatar = saved_url
        elif avatar_type == "url" and request.form.get("avatar_url", "").strip():
            avatar = request.form.get("avatar_url", "").strip()
        elif request.form.get("avatar", "").strip():
            avatar = request.form.get("avatar", "").strip()

        auth_service.update_profile(current_user, bio=bio, avatar=avatar)
        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for("users.profile", username=current_user.username))

    return render_template("users/edit.html", user=current_user)
