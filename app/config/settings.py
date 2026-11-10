import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Importar configuración de IA
from app.config.ai_config import (
    AI_PROVIDER,
    AI_MODEL,
    SUPPORTED_PROVIDERS,
    OLLAMA_DEFAULT_MODEL,
    OPENROUTER_DEFAULT_MODEL,
    OLLAMA_ENDPOINTS,
    SELECTED_OLLAMA_ENDPOINT,
    OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY,
    AI_PROVIDER_URL,
    resolve_provider_url,
    resolve_model,
)


class Config:
    """Configuración base de la aplicación Flask."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key-ia-assistant")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "ia_assistant")

    # =========================================================================
    # Configuración de Proveedores de IA (OpenRouter y Ollama)
    # =========================================================================
    AI_PROVIDER = AI_PROVIDER  # 'ollama' u 'openrouter'
    AI_MODEL = AI_MODEL        # Modelo a utilizar
    SUPPORTED_PROVIDERS = SUPPORTED_PROVIDERS
    OLLAMA_DEFAULT_MODEL = OLLAMA_DEFAULT_MODEL
    OPENROUTER_DEFAULT_MODEL = OPENROUTER_DEFAULT_MODEL
    OLLAMA_ENDPOINTS = OLLAMA_ENDPOINTS
    SELECTED_OLLAMA_ENDPOINT = SELECTED_OLLAMA_ENDPOINT
    OPENROUTER_BASE_URL = OPENROUTER_BASE_URL
    OPENROUTER_API_KEY = OPENROUTER_API_KEY
    AI_PROVIDER_URL = AI_PROVIDER_URL

    resolve_provider_url = staticmethod(resolve_provider_url)
    resolve_model = staticmethod(resolve_model)

    # Compatibilidad histórica
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo."""
    DEBUG = True


class TestingConfig(Config):
    """Configuración para pruebas automatizadas."""
    TESTING = True
    MONGO_DATABASE = "ia_assistant_test"
    SECRET_KEY = "test-secret-key"
    OPENROUTER_API_KEY = "test-openrouter-key"


class ProductionConfig(Config):
    """Configuración para entorno de producción."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

