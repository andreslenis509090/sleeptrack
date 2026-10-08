"""Router para endpoints de gestión de cuenta y usuario (RF01, RF10).

Sigue el patrón Router -> Service -> Repository.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_auth_service, get_current_user_id
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cuenta propia y todos los datos en cascada (RF10)",
    responses={
        204: {"description": "Cuenta y datos eliminados exitosamente en cascada."},
        400: {"description": "Falta confirmación explícita (confirmar=true requerido)."},
        401: {"description": "No autorizado. Token de sesión requerido."},
    },
)
def delete_account(
    user_id: Annotated[str, Depends(get_current_user_id)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    confirmar: bool = Query(
        False,
        description="Confirmación obligatoria para eliminar definitivamente la cuenta y todos los datos asociados.",
    ),
) -> None:
    """Elimina la cuenta del usuario autenticado en Supabase Auth y en cascada todos sus datos (RF10).

    - Requiere confirmación explícita mediante el query parameter `confirmar=true`.
    - La operación utiliza las capacidades de administración con `service_role` en Supabase Auth.
    - Las restricciones `ON DELETE CASCADE` de PostgreSQL eliminan automáticamente el perfil
      en `perfiles_usuario` y todos los registros en `registros_sueno`.
    """
    if not confirmar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Debe confirmar explícitamente la eliminación de la cuenta pasando confirmar=true.",
                "code": "CONFIRMATION_REQUIRED",
            },
        )

    auth_service.delete_user(user_id=user_id)
