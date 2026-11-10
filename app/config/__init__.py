from .settings import config_by_name, Config
from .ai_config import (
    AI_PROVIDER,
    AI_MODEL,
    SUPPORTED_PROVIDERS,
    OLLAMA_ENDPOINTS,
    SELECTED_OLLAMA_ENDPOINT,
    OPENROUTER_BASE_URL,
    resolve_provider_url,
    resolve_model,
)

__all__ = [
    "config_by_name",
    "Config",
    "AI_PROVIDER",
    "AI_MODEL",
    "SUPPORTED_PROVIDERS",
    "OLLAMA_ENDPOINTS",
    "SELECTED_OLLAMA_ENDPOINT",
    "OPENROUTER_BASE_URL",
    "resolve_provider_url",
    "resolve_model",
]

