"""
Pruebas exhaustivas para AIService:
- Reintentos con backoff exponencial para 503 / alta demanda.
- No reintentos y mensaje específico para agotamiento de créditos/cuota.
- No reintentos y mensaje específico para clave inválida.
- No reintentos para permisos denegados o filtros de seguridad.
"""
from unittest.mock import MagicMock, patch
from app.services.ai_service import AIService, GeminiErrorCategory


class FakeAPIError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code
        self.message = message


def test_retry_on_503_overloaded_succeeds_on_second_attempt():
    """Verifica que ante un error 503/sobrecarga, el servicio reintente y tenga éxito en el siguiente intento."""
    ai = AIService(api_key="fake-test-key", max_retries=2, initial_delay=0.01)

    mock_client = MagicMock()
    # Primer intento lanza 503 / UNAVAILABLE, segundo intento responde exitosamente
    mock_resp = MagicMock()
    mock_resp.text = "Respuesta generada tras reintento exitoso."

    mock_client.models.generate_content.side_effect = [
        FakeAPIError("503 The model is overloaded. Please try again later.", code=503),
        mock_resp
    ]

    with patch.object(ai, '_get_client', return_value=mock_client), patch('time.sleep', return_value=None) as mock_sleep:
        text, success, err = ai.generate_response(
            system_prompt="Eres un tutor.",
            messages=[{"role": "user", "content": "¿Qué es Python?"}]
        )

        assert success is True
        assert err is None
        assert text == "Respuesta generada tras reintento exitoso."
        assert mock_client.models.generate_content.call_count == 2
        assert mock_sleep.called


def test_retry_on_503_exhausts_retries():
    """Verifica que si el error 503 persiste tras agotar los reintentos, devuelva el mensaje específico de alta demanda."""
    ai = AIService(api_key="fake-test-key", max_retries=2, initial_delay=0.01)

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = FakeAPIError("503 Service Unavailable / Model is overloaded", code=503)

    with patch.object(ai, '_get_client', return_value=mock_client), patch('time.sleep', return_value=None):
        text, success, err = ai.generate_response(
            system_prompt="Eres un tutor.",
            messages=[{"role": "user", "content": "Hola"}]
        )

        assert success is False
        assert "503" in text or "alta demanda" in text.lower() or "sobrecarga" in text.lower()
        # Se realizaron max_retries + 1 intentos (1 inicial + 2 reintentos = 3)
        assert mock_client.models.generate_content.call_count == 3


def test_no_retry_on_quota_or_credits_exhausted():
    """Verifica que ante falta de créditos o cuota agotada, NO se reintente y se devuelva el mensaje claro de créditos."""
    ai = AIService(api_key="fake-test-key", max_retries=3, initial_delay=0.01)

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = FakeAPIError(
        "RESOURCE_EXHAUSTED: You have exceeded your current quota, please check your plan and billing details.",
        code=429
    )

    with patch.object(ai, '_get_client', return_value=mock_client), patch('time.sleep') as mock_sleep:
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente.",
            messages=[{"role": "user", "content": "Genera un resumen"}]
        )

        assert success is False
        assert "cuota" in text.lower() or "créditos" in text.lower() or "billing" in text.lower()
        # DEBE haber sido llamado SOLO 1 vez (sin reintentos inútiles)
        assert mock_client.models.generate_content.call_count == 1
        assert not mock_sleep.called


def test_no_retry_on_invalid_api_key():
    """Verifica que ante clave de API inválida, NO se reintente."""
    ai = AIService(api_key="fake-test-key", max_retries=3, initial_delay=0.01)

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = FakeAPIError(
        "API_KEY_INVALID: API key not valid. Please pass a valid API key.",
        code=401
    )

    with patch.object(ai, '_get_client', return_value=mock_client), patch('time.sleep') as mock_sleep:
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente.",
            messages=[{"role": "user", "content": "Hola"}]
        )

        assert success is False
        assert "clave de api" in text.lower() or "inválida" in text.lower()
        assert mock_client.models.generate_content.call_count == 1
        assert not mock_sleep.called


def test_no_retry_on_safety_filter():
    """Verifica que ante bloqueo por filtro de seguridad, NO se reintente."""
    ai = AIService(api_key="fake-test-key", max_retries=3, initial_delay=0.01)

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = FakeAPIError(
        "Blocked by safety filters due to HARM_CATEGORY_DANGEROUS_CONTENT",
        code=400
    )

    with patch.object(ai, '_get_client', return_value=mock_client), patch('time.sleep') as mock_sleep:
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente.",
            messages=[{"role": "user", "content": "Test"}]
        )

        assert success is False
        assert "seguridad" in text.lower() or "filtro" in text.lower()
        assert mock_client.models.generate_content.call_count == 1
        assert not mock_sleep.called


# ==============================================================================
# PRUEBAS ESPECÍFICAS DE OLLAMA Y OPENROUTER
# ==============================================================================

from app.config.ai_config import (
    resolve_provider_url,
    resolve_model,
    OLLAMA_ENDPOINTS,
    SUPPORTED_PROVIDERS,
)
import requests


def test_provider_restriction():
    """Verifica que los únicos proveedores soportados sean 'ollama' y 'openrouter'."""
    assert "ollama" in SUPPORTED_PROVIDERS
    assert "openrouter" in SUPPORTED_PROVIDERS
    assert len(SUPPORTED_PROVIDERS) == 2

    ai = AIService()
    # Si se pasa un proveedor no soportado, AIService recurre de forma segura a 'ollama'
    assert ai._get_effective_provider("unsupported_provider") == "ollama"
    assert ai._get_effective_provider("openrouter") == "openrouter"
    assert ai._get_effective_provider("ollama") == "ollama"


def test_ollama_local_url_resolution():
    """Verifica la resolución por defecto de Ollama a http://localhost:11434."""
    url = resolve_provider_url("ollama", selected_ollama="local")
    assert url == "http://localhost:11434"


def test_ollama_multiple_endpoints_resolution():
    """Verifica la selección entre varios servidores de Ollama (LAN, GPU, etc.)."""
    # 1. Servidor LAN 1
    url_lan1 = resolve_provider_url("ollama", selected_ollama="server_lan_1")
    assert "192.168.1.50" in url_lan1

    # 2. Servidor GPU
    url_gpu = resolve_provider_url("ollama", selected_ollama="server_gpu")
    assert "10.0.0.5" in url_gpu

    # 3. URL directa ingresada por el usuario
    custom_direct_url = "http://192.168.1.222:11434"
    url_custom = resolve_provider_url("ollama", selected_ollama=custom_direct_url)
    assert url_custom == custom_direct_url


def test_model_resolution_and_override():
    """Verifica la resolución y modificación sencilla del modelo a utilizar."""
    # Modelo explícito
    assert resolve_model("ollama", model_override="mistral") == "mistral"
    assert resolve_model("openrouter", model_override="deepseek/deepseek-chat") == "deepseek/deepseek-chat"


def test_ollama_native_api_chat_success():
    """Verifica la llamada exitosa al endpoint /api/chat de Ollama."""
    ai = AIService(provider="ollama", provider_url="http://localhost:11434", model="llama3.2")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "llama3.2",
        "message": {"role": "assistant", "content": "¡Hola desde Ollama local!"},
        "done": True
    }

    with patch.object(ai.session, 'post', return_value=mock_resp) as mock_post:
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente amigable.",
            messages=[{"role": "user", "content": "Hola Ollama"}]
        )

        assert success is True
        assert err is None
        assert text == "¡Hola desde Ollama local!"
        assert mock_post.called

        called_url = mock_post.call_args[0][0]
        assert "http://localhost:11434/api/chat" in called_url
        called_json = mock_post.call_args[1]["json"]
        assert called_json["model"] == "llama3.2"


def test_ollama_fallback_to_openai_endpoint():
    """Verifica el fallback automático de Ollama a /v1/chat/completions si /api/chat devuelve 404."""
    ai = AIService(provider="ollama", provider_url="http://localhost:11434", model="llama3.2")

    resp_404 = MagicMock()
    resp_404.status_code = 404

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Respuesta vía OpenAI endpoint en Ollama"}}]
    }

    with patch.object(ai.session, 'post', side_effect=[resp_404, resp_200]):
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente.",
            messages=[{"role": "user", "content": "Test"}]
        )

        assert success is True
        assert text == "Respuesta vía OpenAI endpoint en Ollama"


def test_ollama_connection_error_gives_clear_message():
    """Verifica que ante un fallo de conexión local con Ollama se informe cómo iniciarlo."""
    ai = AIService(provider="ollama", provider_url="http://localhost:11434", model="llama3.2", max_retries=0)

    with patch.object(ai.session, 'post', side_effect=requests.exceptions.ConnectionError("Connection refused")):
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente.",
            messages=[{"role": "user", "content": "Hola"}]
        )

        assert success is False
        assert "ollama" in text.lower()
        assert "servidor" in text.lower() or "conexión" in text.lower()


def test_openrouter_success():
    """Verifica la llamada exitosa a OpenRouter con header Bearer y URL de chat."""
    ai = AIService(
        provider="openrouter",
        provider_url="https://openrouter.ai/api/v1",
        model="meta-llama/llama-3.3-70b-instruct",
        api_key="sk-or-test-key-12345"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Respuesta desde OpenRouter cloud"}}]
    }

    with patch.object(ai.session, 'post', return_value=mock_resp) as mock_post:
        text, success, err = ai.generate_response(
            system_prompt="Eres un asistente experto.",
            messages=[{"role": "user", "content": "Explica la relatividad"}]
        )

        assert success is True
        assert text == "Respuesta desde OpenRouter cloud"

        headers = mock_post.call_args[1]["headers"]
        assert "Bearer sk-or-test-key-12345" in headers["Authorization"]
        called_url = mock_post.call_args[0][0]
        assert "https://openrouter.ai/api/v1/chat/completions" in called_url

