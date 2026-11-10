import re
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """
    Servicio encargado de la lógica de autenticación, registro y validación de usuarios.
    """
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()

    def register(self, email: str, username: str, password: str, bio: str = "", avatar: str = None) -> tuple[User | None, str | None]:
        """
        Registra un nuevo usuario validando campos obligatorios y duplicados.
        Retorna (usuario_creado, mensaje_error).
        """
        # Validaciones de campos
        if not email or not email.strip():
            return None, "El correo electrónico es obligatorio."
        if not username or not username.strip():
            return None, "El nombre de usuario es obligatorio."
        if not password or len(password) < 6:
            return None, "La contraseña debe tener al menos 6 caracteres."

        email_clean = email.strip().lower()
        username_clean = username.strip()

        # Validación básica de formato de correo
        email_regex = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(email_regex, email_clean):
            return None, "El formato del correo electrónico es inválido."

        # Validación de username (caracteres alfanuméricos y guiones)
        if not re.match(r"^[a-zA-Z0-9_\-\.]{3,30}$", username_clean):
            return None, "El nombre de usuario debe tener entre 3 y 30 caracteres (letras, números, _, -, .)."

        # Comprobar unicidad
        if self.user_repo.find_by_email(email_clean):
            return None, "El correo electrónico ya se encuentra registrado."
        if self.user_repo.find_by_username(username_clean):
            return None, "El nombre de usuario ya se encuentra en uso."

        # Crear y persistir usuario
        user = User(
            email=email_clean,
            username=username_clean,
            bio=bio.strip() if bio else "",
            avatar=avatar or "👤",
        )
        user.set_password(password)
        created_user = self.user_repo.create(user)
        return created_user, None

    def authenticate(self, identifier: str, password: str) -> tuple[User | None, str | None]:
        """
        Autentica un usuario por email o username.
        Retorna (usuario, mensaje_error).
        """
        if not identifier or not password:
            return None, "Por favor ingresa tu usuario/correo y contraseña."

        clean_id = identifier.strip()
        user = None

        # Intentar buscar por correo si parece email, de lo contrario por username
        if "@" in clean_id:
            user = self.user_repo.find_by_email(clean_id)
        
        if not user:
            user = self.user_repo.find_by_username(clean_id)

        if not user:
            return None, "Credenciales incorrectas. Verifica tus datos."

        if not user.check_password(password):
            return None, "Credenciales incorrectas. Verifica tus datos."

        return user, None

    def get_user_by_id(self, user_id) -> User | None:
        return self.user_repo.find_by_id(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        return self.user_repo.find_by_username(username)

    def update_profile(self, user: User, bio: str, avatar: str) -> bool:
        user.bio = bio.strip() if bio else ""
        if avatar:
            user.avatar = avatar.strip()
        return self.user_repo.update(user)
