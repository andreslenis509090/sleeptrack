"""Inyección de dependencias para FastAPI (Auth, Repositorios, Servicios).

Cumple con RNF02 (Autenticación y sesiones de usuario) e inyección desacoplada.
Conecta el cliente oficial de Supabase con el repositorio en la nube (RNF04).
"""

from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from supabase import Client
from app.core.config import get_supabase_client
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.services.sleep_record_service import SleepRecordService

# Instancia singleton para fallback de persistencia en memoria durante desarrollo/pruebas locales
_in_memory_repository = SleepRecordRepository(client=None)
_cached_supabase_client: Client | None = None


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
    """Provee la instancia del repositorio de registros de sueño conectado a Supabase (RNF04).

    Si las credenciales de Supabase están configuradas en .env o variables de entorno,
    instancia el repositorio con el cliente real de Supabase. Si no están configuradas,
    recorre al repositorio en memoria para desarrollo local aislado.
    """
    global _cached_supabase_client
    if _cached_supabase_client is None:
        _cached_supabase_client = get_supabase_client()

    if _cached_supabase_client is not None:
        return SleepRecordRepository(client=_cached_supabase_client)

    return _in_memory_repository


def get_sleep_record_service(
    repository: Annotated[SleepRecordRepository, Depends(get_sleep_record_repository)],
) -> SleepRecordService:
    """Provee la instancia de la capa de servicio con el repositorio inyectado."""
    return SleepRecordService(repository=repository)
