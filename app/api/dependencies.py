"""Inyección de dependencias para FastAPI (Auth, Repositorios, Servicios).

Cumple con RNF02 (Autenticación con sesiones y expiración) e inyección desacoplada.
Conecta el cliente oficial de Supabase con los repositorios en la nube (RNF04).
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from supabase import Client

from app.core.config import get_supabase_client, settings
from app.core.exceptions import InvalidTokenError
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.auth_service import AuthService
from app.services.sleep_record_service import SleepRecordService

_cached_supabase_client: Client | None = None
_client_initialized: bool = False


def _get_supabase_client() -> Client | None:
    """Obtiene el cliente Supabase (singleton con inicialización perezosa)."""
    global _cached_supabase_client, _client_initialized
    if not _client_initialized:
        _cached_supabase_client = get_supabase_client()
        _client_initialized = True
    return _cached_supabase_client


# ============================================================================
# Repositorios
# ============================================================================


def get_user_profile_repository() -> UserProfileRepository:
    """Provee el repositorio de perfiles de usuario conectado a Supabase (RNF04)."""
    client = _get_supabase_client()
    return UserProfileRepository(client=client, is_test_mode=settings.is_testing_mode)


def get_sleep_record_repository() -> SleepRecordRepository:
    """Provee el repositorio de registros de sueño conectado a Supabase (RNF04)."""
    client = _get_supabase_client()
    return SleepRecordRepository(client=client)


# ============================================================================
# Servicios
# ============================================================================


def get_auth_service(
    profile_repo: Annotated[UserProfileRepository, Depends(get_user_profile_repository)],
) -> AuthService:
    """Provee el servicio de autenticación con Supabase Auth (RF01, RF02, RNF01, RNF02)."""
    client = _get_supabase_client()
    return AuthService(
        client=client,
        profile_repo=profile_repo,
        is_test_mode=settings.is_testing_mode,
    )


def get_sleep_record_service(
    repository: Annotated[SleepRecordRepository, Depends(get_sleep_record_repository)],
) -> SleepRecordService:
    """Provee la instancia de la capa de servicio de registros de sueño."""
    return SleepRecordService(repository=repository)


# ============================================================================
# Autenticación (RNF02)
# ============================================================================


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> str:
    """Extrae y valida el usuario autenticado a partir del header Authorization (RNF02).

    Requiere un token Bearer válido de Supabase Auth.
    Retorna el UUID (str) del usuario autenticado.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Se requiere autenticación. Incluya el header Authorization: Bearer <token>.",
                "code": "MISSING_TOKEN",
            },
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Formato de autorización inválido. Use: Bearer <token>.",
                "code": "INVALID_TOKEN_FORMAT",
            },
        )

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token vacío.",
                "code": "EMPTY_TOKEN",
            },
        )

    try:
        return auth_service.get_user_id_from_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token de sesión inválido o expirado.",
                "code": "INVALID_TOKEN",
            },
        )
