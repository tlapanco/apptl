from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.chat_service import ChatService
from app.services.personality_service import PersonalityService

chats_bp = Blueprint("chats", __name__, url_prefix="/chats")
chat_service = ChatService()
personality_service = PersonalityService()


@chats_bp.route("", methods=["GET"])
@login_required
def index():
    chats = chat_service.get_user_chats(current_user._id)
    system_personalities = personality_service.get_system_personalities()
    my_personalities = personality_service.get_user_personalities(current_user._id)
    return render_template(
        "chats/index.html",
        chats=chats,
        system_personalities=system_personalities,
        my_personalities=my_personalities
    )


@chats_bp.route("", methods=["POST"])
@login_required
def create():
    personality_id = request.form.get("personality_id")
    version_number = request.form.get("version_number")
    if not personality_id and request.is_json:
        personality_id = request.json.get("personality_id")
        version_number = request.json.get("version_number")

    if not personality_id:
        flash("Debes seleccionar una personalidad para iniciar la conversación.", "warning")
        return redirect(url_for("dashboard.index")), 400

    chat, error = chat_service.create_chat(current_user._id, personality_id, version_number=version_number)
    if error or not chat:
        flash(error or "No se pudo crear la conversación.", "danger")
        return redirect(url_for("dashboard.index")), 403

    if request.is_json:
        return jsonify({"success": True, "chat_id": chat.id, "redirect_url": url_for("chats.view_chat", chat_id=chat.id)})

    return redirect(url_for("chats.view_chat", chat_id=chat.id))


@chats_bp.route("/<chat_id>", methods=["GET"])
@login_required
def view_chat(chat_id):
    chat, error = chat_service.get_chat(current_user._id, chat_id)
    if error or not chat:
        flash(error or "Conversación no encontrada.", "warning")
        return redirect(url_for("dashboard.index")), 404

    user_chats = chat_service.get_user_chats(current_user._id)
    linked_personality = None
    if chat.personality_id:
        linked_personality = personality_service.get_personality(chat.personality_id)

    return render_template(
        "chats/chat.html",
        active_chat=chat,
        chats=user_chats,
        personality=linked_personality
    )


@chats_bp.route("/<chat_id>/sync_personality", methods=["POST"])
@login_required
def sync_personality(chat_id):
    target_version = request.form.get("version")
    if not target_version and request.is_json:
        target_version = request.json.get("version")

    updated_chat, error = chat_service.sync_personality(
        current_user._id,
        chat_id,
        target_version=target_version
    )

    if error:
        if request.is_json:
            return jsonify({"success": False, "error": error}), 400
        flash(error, "danger")
        return redirect(url_for("chats.view_chat", chat_id=chat_id))

    if request.is_json:
        return jsonify({
            "success": True,
            "version": updated_chat.personality_version,
            "snapshot": updated_chat.personality_snapshot,
            "message": "Personalidad y avatar actualizados exitosamente en este chat."
        })

    flash("¡Personalidad y avatar actualizados exitosamente en este chat!", "success")
    return redirect(url_for("chats.view_chat", chat_id=chat_id))


@chats_bp.route("/<chat_id>/messages", methods=["POST"])
@login_required
def send_message(chat_id):
    content = ""
    if request.is_json:
        content = request.json.get("content") or request.json.get("message", "")
    else:
        content = request.form.get("content") or request.form.get("message", "")

    if not content or not content.strip():
        return jsonify({"success": False, "error": "El mensaje no puede estar vacío."}), 400

    assistant_msg, error = chat_service.send_message(
        user_id=current_user._id,
        chat_id=chat_id,
        content=content
    )

    if error:
        return jsonify({"success": False, "error": error}), 500

    msg_data = {
        "role": assistant_msg["role"],
        "content": assistant_msg["content"],
        "created_at": assistant_msg["created_at"].isoformat() if hasattr(assistant_msg["created_at"], "isoformat") else str(assistant_msg["created_at"])
    }

    return jsonify({
        "success": True,
        "message": msg_data,
        "assistant_message": msg_data
    })


@chats_bp.route("/<chat_id>/delete", methods=["POST"])
@login_required
def delete(chat_id):
    success, error = chat_service.delete_chat(current_user._id, chat_id)
    if not success:
        flash(error or "No se pudo eliminar la conversación.", "danger")
    else:
        flash("Conversación eliminada correctamente.", "info")
    return redirect(url_for("dashboard.index"))
