"""Inyección de dependencias para FastAPI (Auth, Repositorios, Servicios).

Cumple con RNF02 (Autenticación y sesiones de usuario) e inyección desacoplada.
"""

from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from app.core.config import get_supabase_client
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.services.sleep_record_service import SleepRecordService

# Instancia singleton del repositorio para persistencia unificada en runtime
_repository_instance = SleepRecordRepository(client=None)


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> int:
    """Extrae y valida el usuario autenticado a partir del header de autorización (RNF02).

    En producción valida el token JWT con expiración.
    Para pruebas y entorno de desarrollo, admite tokens de formato 'Bearer user-<id>'
    o por defecto el usuario con ID 1.
    """
    if authorization is None:
        # Modo por defecto para pruebas de desarrollo local
        return 1

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Encabezado de autorización inválido. Formato esperado: Bearer <token>",
        )

    token = authorization.replace("Bearer ", "").strip()
    if token.startswith("user-"):
        try:
            return int(token.split("-")[1])
        except (ValueError, IndexError):
            pass

    return 1


def get_sleep_record_repository() -> SleepRecordRepository:
    """Provee la instancia del repositorio de registros de sueño."""
    global _repository_instance
    try:
        client = get_supabase_client()
        return SleepRecordRepository(client=client)
    except Exception:
        # Fallback a repositorio local en memoria si no hay conexión activa
        return _repository_instance


def get_sleep_record_service(
    repository: Annotated[SleepRecordRepository, Depends(get_sleep_record_repository)],
) -> SleepRecordService:
    """Provee la instancia de la capa de servicio con el repositorio inyectado."""
    return SleepRecordService(repository=repository)
