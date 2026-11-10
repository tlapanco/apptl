from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
auth_service = AuthService()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        bio = request.form.get("bio", "").strip()
        avatar = request.form.get("avatar", "👤")

        user, error = auth_service.register(
            email=email,
            username=username,
            password=password,
            bio=bio,
            avatar=avatar
        )

        if error:
            flash(error, "danger")
            return render_template("auth/register.html", email=email, username=username, bio=bio, avatar=avatar), 400

        login_user(user)
        flash(f"¡Bienvenido a la plataforma, @{user.username}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user, error = auth_service.authenticate(identifier, password)

        if error or not user:
            flash(error or "Credenciales incorrectas.", "danger")
            return render_template("auth/login.html", identifier=identifier), 401

        login_user(user, remember=remember)
        flash(f"Hola de nuevo, @{user.username}", "info")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("auth.login"))
