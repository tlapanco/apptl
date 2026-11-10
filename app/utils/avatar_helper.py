"""
Utilidades para gestión y renderizado de Avatares (Emojis e Imágenes).
"""

import os
import uuid
from markupsafe import Markup, escape
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def is_allowed_image(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_avatar_file(file_storage, base_static_dir: str = None) -> tuple[str | None, str | None]:
    """
    Guarda un archivo de imagen subido de forma segura.
    Retorna: (url_relativa, error)
    """
    if not file_storage or not file_storage.filename:
        return None, None

    filename = secure_filename(file_storage.filename)
    if not is_allowed_image(filename):
        return None, "Formato de imagen no permitido. Usa PNG, JPG, JPEG, GIF, WEBP o SVG."

    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"avatar_{uuid.uuid4().hex[:12]}.{ext}"

    if not base_static_dir:
        # Ruta estándar en la app
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_static_dir = os.path.join(os.path.dirname(current_dir), "static")

    upload_dir = os.path.join(base_static_dir, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    target_path = os.path.join(upload_dir, unique_name)
    try:
        file_storage.save(target_path)
        return f"/static/uploads/avatars/{unique_name}", None
    except Exception as e:
        return None, f"Error al guardar la imagen: {str(e)}"


def is_image_avatar(avatar_val: str) -> bool:
    """Verifica si un valor de avatar es una URL o ruta de archivo de imagen."""
    if not avatar_val or not isinstance(avatar_val, str):
        return False
    avatar_val = avatar_val.strip()
    if avatar_val.startswith(("http://", "https://", "/static/", "data:image/")):
        return True
    lower = avatar_val.lower()
    for ext in ALLOWED_EXTENSIONS:
        if lower.endswith(f".{ext}"):
            return True
    return False


def render_avatar_html(avatar_val: str, class_name: str = "", default: str = "🤖") -> Markup:
    """
    Renderiza un avatar en HTML de forma segura, soportando imágenes y emojis.
    """
    if not avatar_val:
        avatar_val = default

    if is_image_avatar(avatar_val):
        safe_src = escape(avatar_val)
        safe_class = escape(class_name)
        safe_default = escape(default)
        html = (
            f'<img src="{safe_src}" alt="Avatar" class="avatar-image {safe_class}" '
            f'onerror="this.style.display=\'none\'; if(this.nextElementSibling) this.nextElementSibling.style.display=\'inline-flex\';" loading="lazy" />'
            f'<span class="avatar-fallback {safe_class}" style="display:none;">{safe_default}</span>'
        )
        return Markup(html)
    else:
        safe_emoji = escape(avatar_val)
        safe_class = escape(class_name)
        html = f'<span class="avatar-emoji {safe_class}">{safe_emoji}</span>'
        return Markup(html)
