from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
login_manager.login_message_category = "warning"
