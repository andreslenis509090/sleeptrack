"""Router para el Módulo de Autenticación (RF01, RF02, RNF01, RNF02).

Define los endpoints HTTP de registro y login.
No contiene lógica de negocio ni interactúa directamente con la persistencia.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_service
from app.core.exceptions import AuthenticationError, UserAlreadyExistsError
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserProfileResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario (RF01, RNF01, RNF02)",
    responses={
        201: {"description": "Usuario registrado exitosamente con sesión activa."},
        409: {"description": "Ya existe un usuario con este correo electrónico."},
        422: {"description": "Error de validación en los datos de registro."},
    },
)
def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Registra un nuevo usuario creando su perfil (RF01).

    - La contraseña se almacena cifrada en Supabase Auth (RNF01).
    - Retorna un token de sesión con expiración (RNF02).
    - Los datos de perfil (nombre, apellido, ocupación, metaSueño) se guardan
      en la tabla perfiles_usuario vinculada al UUID de Supabase Auth.
    """
    try:
        result = auth_service.register(
            email=payload.email,
            password=payload.password,
            nombre=payload.nombre,
            apellido=payload.apellido,
            ocupacion=payload.ocupacion,
            meta_sueno=payload.meta_sueno or 8.0,
        )
        user_profile = result["user"]
        return AuthResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=UserProfileResponse(
                id=user_profile.id,
                email=user_profile.email,
                nombre=user_profile.nombre,
                apellido=user_profile.apellido,
                ocupacion=user_profile.ocupacion,
                meta_sueno=user_profile.meta_sueno,
            ),
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticación de usuario (RF02, RNF02)",
    responses={
        200: {"description": "Autenticación exitosa con token de sesión."},
        401: {"description": "Credenciales inválidas."},
        422: {"description": "Error de validación en los datos de login."},
    },
)
def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Autentica un usuario con correo y contraseña (RF02).

    - Supabase Auth valida la contraseña cifrada (RNF01).
    - Retorna un token de sesión con expiración (RNF02).
    """
    try:
        result = auth_service.login(
            email=payload.email,
            password=payload.password,
        )
        user_profile = result["user"]
        return AuthResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=UserProfileResponse(
                id=user_profile.id,
                email=user_profile.email,
                nombre=user_profile.nombre,
                apellido=user_profile.apellido,
                ocupacion=user_profile.ocupacion,
                meta_sueno=user_profile.meta_sueno,
            ),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
