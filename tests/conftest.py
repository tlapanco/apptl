"""
Configuración de fixtures para pruebas con Pytest y mongomock.
"""

import pytest
import mongomock
from app import create_app
from app.extensions.mongo import mongo
from app.services.auth_service import AuthService
from app.services.personality_service import PersonalityService
from app.services.chat_service import ChatService
from app.services.friendship_service import FriendshipService
from app.services.community_service import CommunityService


@pytest.fixture
def app():
    """Crea una aplicación Flask en modo testing."""
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'MONGODB_URI': 'mongodb://localhost:27017/test_db',
        'MONGODB_DB_NAME': 'test_persona_ai_db',
        'GEMINI_API_KEY': 'test_gemini_key',
        'WTF_CSRF_ENABLED': False
    }

    # Inicializar aplicación
    application = create_app(config_override=test_config)

    # Configurar base de datos mock para pruebas aisladas
    mock_client = mongomock.MongoClient()
    mongo.client = mock_client
    mongo.db = mock_client[test_config['MONGODB_DB_NAME']]

    with application.app_context():
        # Ejecutar seed de personalidades
        from seeds.personalities import seed_system_personalities
        seed_system_personalities()
        yield application


@pytest.fixture
def client(app):
    """Cliente HTTP de prueba."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner de comandos CLI."""
    return app.test_cli_runner()


@pytest.fixture
def auth_service(app):
    return AuthService()


@pytest.fixture
def personality_service(app):
    return PersonalityService()


@pytest.fixture
def chat_service(app):
    return ChatService()


@pytest.fixture
def friendship_service(app):
    return FriendshipService()


@pytest.fixture
def community_service(app):
    return CommunityService()


@pytest.fixture
def sample_user(auth_service):
    """Usuario de prueba estándar registrado."""
    user, err = auth_service.register(
        username='testuser',
        email='testuser@example.com',
        password='password123',
        avatar='👨‍💻',
        bio='Tester developer'
    )
    return user


@pytest.fixture
def sample_user2(auth_service):
    """Segundo usuario de prueba."""
    user, err = auth_service.register(
        username='frienduser',
        email='friend@example.com',
        password='password123',
        avatar='👩‍💻',
        bio='Friend developer'
    )
    return user
