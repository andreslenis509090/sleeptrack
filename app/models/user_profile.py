"""Modelo de Dominio para Perfil de Usuario (RF01).

Representa los datos de perfil del usuario (nombre, apellido, ocupación, meta de sueño)
almacenados en la tabla perfiles_usuario, vinculados al usuario de Supabase Auth por UUID.
No almacena contraseñas — esas las gestiona Supabase Auth (RNF01).
"""

from dataclasses import dataclass


@dataclass
class PerfilUsuario:
    """Entidad de dominio para el perfil de usuario según el informe técnico (RF01)."""

    id: str  # UUID de auth.users en Supabase Auth
    email: str
    nombre: str
    apellido: str
    ocupacion: str
    meta_sueno: float | None = None
