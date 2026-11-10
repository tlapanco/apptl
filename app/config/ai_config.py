"""
Configuración dedicada de Proveedores de Inteligencia Artificial (IA) para PersonaAI.

================================================================================
INSTRUCCIONES DE CONFIGURACIÓN RÁPIDA:
================================================================================
1. PROVEEDOR DE IA:
   Únicamente se permite elegir entre:
     - 'ollama'     : Para Ollama ejecutándose de forma local o en red privada.
     - 'openrouter' : Para OpenRouter API (proveedor cloud multi-modelo).

2. MODELO DE IA:
   Modifica 'AI_MODEL' a continuación para elegir el modelo deseado.
   Ejemplos populares para Ollama:
     - 'llama3.2' (por defecto)
     - 'llama3.2:1b'
     - 'llama3'
     - 'mistral'
     - 'deepseek-r1:8b'
     - 'qwen2.5:7b'
     - 'phi3'
   Ejemplos populares para OpenRouter:
     - 'meta-llama/llama-3.3-70b-instruct'
     - 'deepseek/deepseek-chat'
     - 'mistralai/mistral-7b-instruct'
     - 'google/gemini-2.0-flash-001'

3. URL DEL PROVEEDOR / MULTIPLES PROVEEDORES DE OLLAMA:
   Puedes tener varios servidores u ordenadores con Ollama configurados en el diccionario
   'OLLAMA_ENDPOINTS' (ej: tu máquina local, un servidor en LAN con GPU, etc.).
   Para seleccionar cuál usar, cambia 'SELECTED_OLLAMA_ENDPOINT' al nombre de la clave
   (ej. 'local', 'server_lan_1', 'server_gpu') o escribe la URL directa ("http://...").
================================================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 1. SELECCIÓN DEL PROVEEDOR DE IA ACTIVO
# Valores permitidos únicamente: 'ollama' | 'openrouter'
# ==============================================================================
# Por defecto es 'ollama' (local)
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower().strip()

# Validación estricta: solo se admiten 'openrouter' y 'ollama'
SUPPORTED_PROVIDERS = ("ollama", "openrouter")
if AI_PROVIDER not in SUPPORTED_PROVIDERS:
    AI_PROVIDER = "ollama"

# ==============================================================================
# 2. MODELO DE IA A UTILIZAR (FÁCILMENTE MODIFICABLE AQUÍ O VÍA .ENV)
# ==============================================================================
# Cambia esta variable directamente con el nombre del modelo que quieras usar.
AI_MODEL = os.getenv("AI_MODEL", "llama3.2")

# Modelos predeterminados por proveedor (se usan si AI_MODEL estuviera vacío):
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

# ==============================================================================
# 3. CONFIGURACIÓN DE URLS Y MÚLTIPLES ENDPOINTS PARA OLLAMA
# Ollama es local por defecto ('http://localhost:11434').
# Aquí puedes registrar tantos servidores / endpoints como tengas planeados.
# ==============================================================================
OLLAMA_ENDPOINTS = {
    # 1. Servidor local estándar de Ollama
    "local": os.getenv("OLLAMA_LOCAL_URL", "http://localhost:11434"),

    # 2. Servidores adicionales en red local (LAN) o servidores dedicados con GPU
    "server_lan_1": os.getenv("OLLAMA_SERVER_1_URL", "http://192.168.1.50:11434"),
    "server_lan_2": os.getenv("OLLAMA_SERVER_2_URL", "http://192.168.1.100:11434"),
    "server_gpu": os.getenv("OLLAMA_GPU_URL", "http://10.0.0.5:11434"),

    # 3. Endpoint personalizado adicional
    "custom": os.getenv("OLLAMA_CUSTOM_URL", "http://localhost:11434"),
}

# SELECCIÓN DEL ENDPOINT ACTIVO DE OLLAMA:
# Escribe aquí la clave de la lista de arriba ('local', 'server_lan_1', 'server_gpu', 'custom')
# O escribe directamente una URL completa (ej. 'http://192.168.1.200:11434')
SELECTED_OLLAMA_ENDPOINT = os.getenv("SELECTED_OLLAMA_ENDPOINT", "local").strip()

# ==============================================================================
# 4. CONFIGURACIÓN DE OPENROUTER (CLOUD)
# ==============================================================================
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ==============================================================================
# 5. URL DIRECTA DEL PROVEEDOR DE IA (OPCIONAL)
# Si se define, tiene máxima prioridad sobre cualquier URL anterior.
# ==============================================================================
AI_PROVIDER_URL = os.getenv("AI_PROVIDER_URL", "").strip()


def resolve_provider_url(
    provider: str = None,
    selected_ollama: str = None,
    url_override: str = None
) -> str:
    """
    Resuelve la URL correspondiente al proveedor configurado o solicitado.

    Prioridad de resolución:
      1. url_override (pasado explícitamente a la función)
      2. AI_PROVIDER_URL (si está configurado de forma global)
      3. Si el proveedor es 'ollama':
         - Si selected_ollama coincide con una clave en OLLAMA_ENDPOINTS, retorna esa URL.
         - Si selected_ollama es una URL directa (inicia con http:// o https://), la retorna.
         - De lo contrario retorna OLLAMA_ENDPOINTS['local'] ('http://localhost:11434').
      4. Si el proveedor es 'openrouter':
         - Retorna OPENROUTER_BASE_URL ('https://openrouter.ai/api/v1').
    """
    if url_override and url_override.strip():
        return url_override.strip().rstrip("/")

    if AI_PROVIDER_URL:
        return AI_PROVIDER_URL.rstrip("/")

    prov = (provider or AI_PROVIDER).lower().strip()
    if prov == "ollama":
        sel = (selected_ollama or SELECTED_OLLAMA_ENDPOINT).strip()
        if sel in OLLAMA_ENDPOINTS:
            return OLLAMA_ENDPOINTS[sel].rstrip("/")
        if sel.startswith("http://") or sel.startswith("https://"):
            return sel.rstrip("/")
        return OLLAMA_ENDPOINTS.get("local", "http://localhost:11434").rstrip("/")
    elif prov == "openrouter":
        return OPENROUTER_BASE_URL.rstrip("/")

    return OLLAMA_ENDPOINTS.get("local", "http://localhost:11434").rstrip("/")


def resolve_model(provider: str = None, model_override: str = None) -> str:
    """
    Resuelve el modelo a utilizar según el proveedor y las opciones configuradas.
    """
    if model_override and model_override.strip():
        return model_override.strip()

    if AI_MODEL and AI_MODEL.strip():
        return AI_MODEL.strip()

    prov = (provider or AI_PROVIDER).lower().strip()
    if prov == "openrouter":
        return OPENROUTER_DEFAULT_MODEL
    return OLLAMA_DEFAULT_MODEL
