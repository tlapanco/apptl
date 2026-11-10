import os
from flask import Flask, render_template
from datetime import datetime, timezone
from app.config.settings import config_by_name
from app.extensions.mongo import mongo
from app.extensions.login import login_manager
from app.repositories.user_repository import UserRepository
from app.routes.auth import auth_bp
from app.routes.chats import chats_bp
from app.routes.personalities import personalities_bp
from app.routes.community import community_bp
from app.routes.users import users_bp
from app.routes.friendships import friendships_bp
from app.routes.dashboard import dashboard_bp
from seeds.personalities import seed_system_personalities


def create_app(config_name=None, config_override=None):
    """
    Application Factory de Flask.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Determinar configuración
    env = config_name or os.getenv("FLASK_ENV", "development")
    config_class = config_by_name.get(env, config_by_name["default"])
    app.config.from_object(config_class)

    if config_override:
        app.config.update(config_override)

    # Inicializar extensiones
    mongo.init_app(app)
    login_manager.init_app(app)

    # User loader para Flask-Login
    user_repo = UserRepository()

    @login_manager.user_loader
    def load_user(user_id):
        return user_repo.find_by_id(user_id)

    # Registrar Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chats_bp)
    app.register_blueprint(personalities_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(friendships_bp)

    from app.utils.avatar_helper import render_avatar_html, is_image_avatar
    from app.utils.markdown_helper import render_markdown

    # Filtros personalizados para Jinja
    @app.template_filter("avatar_html")
    def avatar_html_filter(avatar_val, default="🤖", class_name=""):
        return render_avatar_html(avatar_val, class_name=class_name, default=default)

    @app.template_filter("is_image_avatar")
    def is_image_avatar_filter(avatar_val):
        return is_image_avatar(avatar_val)

    @app.template_filter("render_markdown")
    def render_markdown_filter(text):
        return render_markdown(text)

    @app.template_filter("markdown_to_html")
    def markdown_to_html_filter(text):
        return render_markdown(text)

    @app.context_processor
    def utility_processor():
        from app.config.ai_config import AI_PROVIDER, resolve_model, resolve_provider_url
        effective_prov = app.config.get("AI_PROVIDER", AI_PROVIDER)
        effective_mod = app.config.get("AI_MODEL") or resolve_model(effective_prov)
        effective_url = app.config.get("AI_PROVIDER_URL") or resolve_provider_url(effective_prov, app.config.get("SELECTED_OLLAMA_ENDPOINT"))
        return dict(
            render_avatar=render_avatar_html,
            is_image_avatar=is_image_avatar,
            render_markdown=render_markdown,
            current_ai_provider=effective_prov,
            current_ai_model=effective_mod,
            current_ai_url=effective_url,
        )

    @app.template_filter("format_date")
    def format_date_filter(dt):
        if not dt:
            return ""
        if isinstance(dt, str):
            return dt
        try:
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(dt)

    @app.template_filter("time_ago")
    def time_ago_filter(dt):
        if not dt:
            return ""
        if isinstance(dt, str):
            return dt
        try:
            now = datetime.now(timezone.utc)
            # Asegurar compatibilidad de timezones
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            diff = now - dt
            seconds = int(diff.total_seconds())

            if seconds < 60:
                return "hace un momento"
            elif seconds < 3600:
                mins = seconds // 60
                return f"hace {mins} min"
            elif seconds < 86400:
                hrs = seconds // 3600
                return f"hace {hrs} h"
            elif seconds < 604800:
                days = seconds // 86400
                return f"hace {days} d"
            else:
                return dt.strftime("%d %b %Y")
        except Exception:
            return str(dt)

    # Manejo de errores HTTP
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("base.html", error_code=400, error_message="Solicitud incorrecta o parámetros inválidos."), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("base.html", error_code=403, error_message="No tienes permiso para acceder a este recurso."), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", error_code=404, error_message="La página o recurso que buscas no existe."), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("base.html", error_code=500, error_message="Ocurrió un problema interno en el servidor."), 500

    # Inicializar semillas de personalidades del sistema de forma automática e idempotente
    with app.app_context():
        try:
            seed_system_personalities()
        except Exception as err:
            app.logger.warning(f"Aviso al inicializar semillas: {err}")

    return app
