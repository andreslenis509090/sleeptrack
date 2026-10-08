"""Esquemas Pydantic v2 para autenticación y perfil de usuario (RF01, RF02, RNF01, RNF02).

Permite tanto nomenclatura snake_case como camelCase para interoperabilidad móvil.
"""

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Esquema de registro de usuario (RF01)."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "estudiante@universidad.edu",
                "password": "miPassword123",
                "nombre": "Andrés",
                "apellido": "Lenis",
                "ocupacion": "Estudiante",
                "metaSueno": 8.0,
            }
        },
    )

    email: str = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres, RNF01)")
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    ocupacion: str = Field(..., min_length=1, max_length=100, alias="ocupacion")
    meta_sueno: float | None = Field(
        default=8.0, ge=1.0, le=24.0, alias="metaSueno",
        description="Meta personal de horas de sueño (RF01, RN03)",
    )


class LoginRequest(BaseModel):
    """Esquema de login (RF02)."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "estudiante@universidad.edu",
                "password": "miPassword123",
            }
        },
    )

    email: str = Field(..., description="Correo electrónico")
    password: str = Field(..., description="Contraseña")


class UserProfileResponse(BaseModel):
    """Perfil del usuario autenticado (RF01)."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="UUID del usuario en Supabase Auth")
    email: str
    nombre: str
    apellido: str
    ocupacion: str
    meta_sueno: float = Field(..., alias="metaSueno")


class AuthResponse(BaseModel):
    """Respuesta de autenticación exitosa con token de sesión (RF01, RF02, RNF02)."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    expires_in: int = Field(..., alias="expiresIn", description="Segundos hasta expiración (RNF02)")
    user: UserProfileResponse
