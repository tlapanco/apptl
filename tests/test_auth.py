"""
Pruebas para el módulo de Autenticación y Usuarios.
"""

from werkzeug.security import check_password_hash


def test_user_registration_success(auth_service):
    user, err = auth_service.register(
        username='alice',
        email='alice@example.com',
        password='securePassword123',
        avatar='👩‍🚀',
        bio='Space enthusiast'
    )
    assert err is None
    assert user is not None
    assert user.username == 'alice'
    assert user.email == 'alice@example.com'
    assert check_password_hash(user.password_hash, 'securePassword123')


def test_user_registration_duplicate_username(auth_service, sample_user):
    user, err = auth_service.register(
        username='testuser',
        email='other@example.com',
        password='password123'
    )
    assert user is None
    assert 'nombre de usuario ya se encuentra en uso' in err


def test_user_registration_duplicate_email(auth_service, sample_user):
    user, err = auth_service.register(
        username='uniquename',
        email='testuser@example.com',
        password='password123'
    )
    assert user is None
    assert 'correo electrónico ya se encuentra registrado' in err


def test_user_registration_short_password(auth_service):
    user, err = auth_service.register(
        username='bob',
        email='bob@example.com',
        password='123'
    )
    assert user is None
    assert 'al menos 6 caracteres' in err


def test_user_authenticate_success(auth_service, sample_user):
    user, err = auth_service.authenticate('testuser', 'password123')
    assert err is None
    assert user is not None
    assert user.username == 'testuser'

    # Autenticación por email
    user2, err2 = auth_service.authenticate('testuser@example.com', 'password123')
    assert err2 is None
    assert user2.id == user.id


def test_user_authenticate_wrong_password(auth_service, sample_user):
    user, err = auth_service.authenticate('testuser', 'wrongpassword')
    assert user is None
    assert err is not None


def test_user_authenticate_nonexistent(auth_service):
    user, err = auth_service.authenticate('nonexistent', 'password123')
    assert user is None
    assert err is not None
