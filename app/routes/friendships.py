from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.friendship_service import FriendshipService

friendships_bp = Blueprint("friendships", __name__, url_prefix="/friendships")
friendship_service = FriendshipService()


@friendships_bp.route("", methods=["GET"])
@login_required
def index():
    data = friendship_service.get_user_friendships_detailed(current_user._id)
    return render_template("friendships/index.html", data=data)


@friendships_bp.route("/request", methods=["POST"])
@login_required
def send_request():
    username = request.form.get("username", "").strip()
    if not username and request.is_json:
        username = request.json.get("username", "").strip()

    friendship, error = friendship_service.send_request(current_user._id, username)
    if error:
        if request.is_json:
            return jsonify({"success": False, "error": error}), 400
        flash(error, "warning")
    else:
        if request.is_json:
            return jsonify({"success": True, "message": f"Solicitud enviada a @{username}"})
        flash(f"Solicitud de amistad enviada a @{username}.", "success")

    return redirect(request.referrer or url_for("friendships.index"))


@friendships_bp.route("/<id>/accept", methods=["POST"])
@login_required
def accept(id):
    success, error = friendship_service.accept_request(current_user._id, id)
    if error:
        flash(error, "danger")
    else:
        flash("Solicitud de amistad aceptada.", "success")
    return redirect(request.referrer or url_for("friendships.index"))


@friendships_bp.route("/<id>/reject", methods=["POST"])
@login_required
def reject(id):
    success, error = friendship_service.reject_request(current_user._id, id)
    if error:
        flash(error, "warning")
    else:
        flash("Solicitud rechazada.", "info")
    return redirect(request.referrer or url_for("friendships.index"))


@friendships_bp.route("/<target_user_id>/remove", methods=["POST"])
@login_required
def remove(target_user_id):
    success, error = friendship_service.remove_friendship(current_user._id, target_user_id)
    if error:
        flash(error, "danger")
    else:
        flash("Amistad eliminada.", "info")
    return redirect(request.referrer or url_for("friendships.index"))
