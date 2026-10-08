"""Pruebas para el módulo de Autenticación y Autorización (RF01, RF02, RNF01, RNF02).

Cubre:
1. Registro exitoso (201).
2. Correo duplicado (409).
3. Login correcto con credenciales válidas (200 con tokens).
4. Login con contraseña incorrecta (401).
5. Acceso a endpoints protegidos de sleep-records sin sesión (401).
6. Validación de fallo claro si faltan variables de Supabase fuera de modo testing.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service, get_user_profile_repository
from app.core.config import Settings
from app.main import app
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.auth_service import AuthService


@pytest.fixture
def auth_repo():
    """Repositorio de perfiles en modo test."""
    return UserProfileRepository(client=None, is_test_mode=True)


@pytest.fixture
def auth_service(auth_repo):
    """Servicio de autenticación en modo test."""
    return AuthService(client=None, profile_repo=auth_repo, is_test_mode=True)


@pytest.fixture
def client(auth_repo, auth_service):
    """TestClient configurado con dependencias de auth aisladas."""
    app.dependency_overrides[get_user_profile_repository] = lambda: auth_repo
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_registro_usuario_exitoso_rf01(client):
    """RF01, RNF01, RNF02: Registro exitoso con retorno de perfil y tokens de sesión."""
    payload = {
        "email": "estudiante.nuevo@universidad.edu",
        "password": "PasswordSegura123",
        "nombre": "Carlos",
        "apellido": "Gómez",
        "ocupacion": "Estudiante de Ingeniería",
        "metaSueno": 7.5,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["tokenType"] == "bearer"
    assert data["expiresIn"] == 3600
    assert data["user"]["email"] == "estudiante.nuevo@universidad.edu"
    assert data["user"]["nombre"] == "Carlos"
    assert data["user"]["apellido"] == "Gómez"
    assert data["user"]["ocupacion"] == "Estudiante de Ingeniería"
    assert data["user"]["metaSueno"] == 7.5
    assert len(data["user"]["id"]) > 0


def test_registro_usuario_correo_duplicado_rechaza_409(client):
    """RF01: Intentar registrar un correo ya existente debe responder HTTP 409 Conflict."""
    payload = {
        "email": "duplicado@universidad.edu",
        "password": "PasswordSegura123",
        "nombre": "Ana",
        "apellido": "López",
        "ocupacion": "Diseñadora",
        "metaSueno": 8.0,
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Segundo intento con el mismo correo
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    data_err = res2.json()
    assert data_err["detail"]["code"] == "USER_ALREADY_EXISTS"


def test_login_correcto_rf02(client):
    """RF02, RNF02: Login con credenciales válidas retorna token de sesión activo."""
    # 1. Registrar usuario
    reg_payload = {
        "email": "login.test@universidad.edu",
        "password": "MiPasswordSegura99",
        "nombre": "Martín",
        "apellido": "Pérez",
        "ocupacion": "Desarrollador",
        "metaSueno": 8.0,
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Login correcto
    login_payload = {
        "email": "login.test@universidad.edu",
        "password": "MiPasswordSegura99",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert "accessToken" in data
    assert data["user"]["email"] == "login.test@universidad.edu"
    assert data["user"]["nombre"] == "Martín"


def test_login_contrasena_incorrecta_rechaza_401_rf02(client):
    """RF02: Login con contraseña incorrecta retorna HTTP 401 Unauthorized."""
    # 1. Registrar usuario
    reg_payload = {
        "email": "fallo.password@universidad.edu",
        "password": "PasswordCorrecta123",
        "nombre": "Lucía",
        "apellido": "Rivas",
        "ocupacion": "Investigadora",
        "metaSueno": 8.0,
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Intentar login con clave errónea
    bad_login = {
        "email": "fallo.password@universidad.edu",
        "password": "PasswordErronea999",
    }
    response = client.post("/api/v1/auth/login", json=bad_login)
    assert response.status_code == 401
    data_err = response.json()
    assert data_err["detail"]["code"] == "INVALID_CREDENTIALS"


def test_sleep_records_sin_sesion_retorna_401():
    """RNF02: Peticiones a endpoints de registros de sueño sin Authorization header retornan 401."""
    # Creamos un cliente limpio sin override de get_current_user_id
    clean_client = TestClient(app)
    response = clean_client.post(
        "/api/v1/sleep-records",
        json={
            "fecha": "2026-10-07",
            "horaAcostarse": "22:00",
            "horaDespertar": "06:00",
            "calificacion": 4,
        },
    )
    assert response.status_code == 401
    data_err = response.json()
    assert data_err["detail"]["code"] == "MISSING_TOKEN"


def test_sleep_records_con_token_invalido_retorna_401(client, auth_service):
    """RNF02: Petición con token inexistente o expirado retorna HTTP 401."""
    response = client.get(
        "/api/v1/sleep-records/by-date/2026-10-07",
        headers={"Authorization": "Bearer token-invalido-xyz"},
    )
    assert response.status_code == 401
    data_err = response.json()
    assert data_err["detail"]["code"] == "INVALID_TOKEN"


def test_modo_produccion_falla_si_faltan_variables_supabase():
    """Ajuste 1: En ejecución normal (sin testing), si client es None debe fallar con error claro."""
    # Verificar que AuthService rechaza client=None cuando is_test_mode=False
    with pytest.raises(RuntimeError) as exc_info_auth:
        AuthService(client=None, profile_repo=None, is_test_mode=False)
    assert "Credenciales de Supabase no configuradas" in str(exc_info_auth.value)

    # Verificar que UserProfileRepository rechaza client=None cuando is_test_mode=False
    with pytest.raises(RuntimeError) as exc_info_repo:
        UserProfileRepository(client=None, is_test_mode=False)
    assert "Credenciales de Supabase no configuradas" in str(exc_info_repo.value)
