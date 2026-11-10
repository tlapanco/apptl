from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.personality_service import PersonalityService
from app.services.auth_service import AuthService
from app.models.personality import Personality
from app.utils.avatar_helper import save_avatar_file, is_image_avatar

personalities_bp = Blueprint("personalities", __name__, url_prefix="/personalities")
personality_service = PersonalityService()
auth_service = AuthService()


@personalities_bp.route("", methods=["GET"])
@login_required
def index():
    my_personalities = personality_service.get_user_personalities(current_user._id)
    system_personalities = personality_service.get_system_personalities()
    liked_ids = personality_service.get_user_liked_ids(current_user._id)

    return render_template(
        "personalities/index.html",
        my_personalities=my_personalities,
        system_personalities=system_personalities,
        liked_ids=liked_ids,
        categories=Personality.DEFAULT_CATEGORIES
    )


@personalities_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        system_prompt = request.form.get("system_prompt", "").strip()
        visibility = request.form.get("visibility", "public")
        category = request.form.get("category", "Otros")
        tags = request.form.get("tags", "")

        # Gestión flexible de Avatar: Archivo > URL > Emoji
        avatar_type = request.form.get("avatar_type", "emoji")
        avatar = "🤖"

        if "avatar_file" in request.files and request.files["avatar_file"].filename:
            saved_url, err = save_avatar_file(request.files["avatar_file"])
            if err:
                flash(err, "danger")
                return render_template(
                    "personalities/create.html",
                    name=name,
                    description=description,
                    system_prompt=system_prompt,
                    avatar=avatar,
                    visibility=visibility,
                    category=category,
                    tags=tags,
                    categories=Personality.DEFAULT_CATEGORIES,
                ), 400
            avatar = saved_url
        elif avatar_type == "url" and request.form.get("avatar_url", "").strip():
            avatar = request.form.get("avatar_url", "").strip()
        else:
            avatar = request.form.get("avatar", "🤖").strip() or "🤖"

        personality, error = personality_service.create_personality(
            user_id=current_user._id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            avatar=avatar,
            visibility=visibility,
            category=category,
            tags=tags,
        )

        if error:
            flash(error, "danger")
            return render_template(
                "personalities/create.html",
                name=name,
                description=description,
                system_prompt=system_prompt,
                avatar=avatar,
                visibility=visibility,
                category=category,
                tags=tags,
                categories=Personality.DEFAULT_CATEGORIES,
            ), 400

        flash("¡Personalidad creada exitosamente!", "success")
        return redirect(url_for("personalities.detail", id=personality.id))

    return render_template("personalities/create.html", categories=Personality.DEFAULT_CATEGORIES)


@personalities_bp.route("/<id>", methods=["GET"])
def detail(id):
    personality = personality_service.get_personality(id)
    if not personality:
        # En lugar de redirigir y romper la experiencia, mostrar la vista informativa de personalidad eliminada
        return render_template("personalities/deleted.html", personality_id=id)

    user_id = current_user._id if current_user.is_authenticated else None
    if not personality_service.can_user_access_personality(user_id, personality):
        flash("No tienes permiso para ver esta personalidad privada.", "danger")
        return redirect(url_for("community.index")), 403

    owner = None
    if personality.owner_id and not personality.is_system:
        owner = auth_service.get_user_by_id(personality.owner_id)

    is_liked = False
    if current_user.is_authenticated:
        liked_ids = personality_service.get_user_liked_ids(current_user._id)
        is_liked = str(personality._id) in liked_ids

    can_edit = personality_service.can_user_edit_personality(user_id, personality)

    return render_template(
        "personalities/detail.html",
        personality=personality,
        owner=owner,
        is_liked=is_liked,
        can_edit=can_edit,
    )


@personalities_bp.route("/<id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    personality = personality_service.get_personality(id)
    if not personality:
        return render_template("personalities/deleted.html", personality_id=id)

    if not personality_service.can_user_edit_personality(current_user._id, personality):
        flash("No estás autorizado para editar esta personalidad.", "danger")
        return redirect(url_for("personalities.detail", id=id)), 403

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        system_prompt = request.form.get("system_prompt", "").strip()
        visibility = request.form.get("visibility", "public")
        category = request.form.get("category", "Otros")
        tags = request.form.get("tags", "")

        # Gestión flexible de Avatar: Archivo > URL > Emoji
        avatar_type = request.form.get("avatar_type", "emoji")
        avatar = personality.avatar or "🤖"

        if "avatar_file" in request.files and request.files["avatar_file"].filename:
            saved_url, err = save_avatar_file(request.files["avatar_file"])
            if err:
                flash(err, "danger")
                return render_template(
                    "personalities/edit.html",
                    personality=personality,
                    categories=Personality.DEFAULT_CATEGORIES,
                ), 400
            avatar = saved_url
        elif avatar_type == "url" and request.form.get("avatar_url", "").strip():
            avatar = request.form.get("avatar_url", "").strip()
        elif request.form.get("avatar", "").strip():
            avatar = request.form.get("avatar", "").strip()

        change_notes = request.form.get("change_notes", "").strip()

        updated, error = personality_service.update_personality(
            user_id=current_user._id,
            personality_id=id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            avatar=avatar,
            visibility=visibility,
            category=category,
            tags=tags,
            change_notes=change_notes,
        )

        if error:
            flash(error, "danger")
            return render_template(
                "personalities/edit.html",
                personality=personality,
                categories=Personality.DEFAULT_CATEGORIES,
            ), 400

        flash(f"Personalidad actualizada correctamente (versión v{updated.current_version}.0).", "success")
        return redirect(url_for("personalities.detail", id=id))

    return render_template(
        "personalities/edit.html",
        personality=personality,
        categories=Personality.DEFAULT_CATEGORIES,
    )


@personalities_bp.route("/<id>/delete", methods=["POST"])
@login_required
def delete(id):
    success, error = personality_service.delete_personality(current_user._id, id)
    if not success:
        flash(error or "No se pudo eliminar la personalidad.", "danger")
        return redirect(url_for("personalities.detail", id=id)), 403

    flash("Personalidad eliminada con éxito.", "info")
    return redirect(url_for("personalities.index"))


@personalities_bp.route("/<id>/like", methods=["POST"])
@login_required
def toggle_like(id):
    is_liked, likes_count, error = personality_service.toggle_like(current_user._id, id)
    if error:
        if request.is_json:
            return jsonify({"success": False, "error": error}), 400
        flash(error, "warning")
        return redirect(request.referrer or url_for("community.index"))

    if request.is_json:
        return jsonify({"success": True, "is_liked": is_liked, "likes_count": likes_count})

    return redirect(request.referrer or url_for("personalities.detail", id=id))
