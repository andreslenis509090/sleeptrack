"""Capa de Servicio para Autenticación y Gestión de Perfiles (RF01, RF02, RNF01, RNF02).

Usa Supabase Auth para manejo de contraseñas cifradas (RNF01) y sesiones con expiración (RNF02).
Las contraseñas NUNCA se almacenan en tablas propias.
Los datos de perfil (nombre, apellido, ocupación, metaSueño) se persisten en perfiles_usuario.

No contiene referencias a frameworks web (Request, Response, HTTPException)
y lanza únicamente excepciones de dominio tipadas.
"""

import uuid

from supabase import Client

from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from app.models.user_profile import PerfilUsuario
from app.repositories.user_profile_repository import UserProfileRepository


class AuthService:
    """Servicio que encapsula la lógica de autenticación y gestión de perfiles."""

    def __init__(
        self,
        client: Client | None,
        profile_repo: UserProfileRepository,
        is_test_mode: bool = False,
    ) -> None:
        if client is None and not is_test_mode:
            raise RuntimeError(
                "Credenciales de Supabase no configuradas. Defina SUPABASE_URL y SUPABASE_KEY en .env "
                "o habilite el modo de pruebas con TESTING=true."
            )
        self.client = client
        self.profile_repo = profile_repo
        self._test_mode = is_test_mode
        # Almacenamiento en memoria para modo de pruebas sin Supabase
        self._test_users: dict[str, dict] = {}  # email -> {id, email, password}
        self._test_tokens: dict[str, str] = {}  # token -> user_id

    def register(
        self,
        email: str,
        password: str,
        nombre: str,
        apellido: str,
        ocupacion: str,
        meta_sueno: float = 8.0,
    ) -> dict:
        """Registra un nuevo usuario con Supabase Auth y crea su perfil (RF01, RNF01).

        Retorna dict con: access_token, refresh_token, token_type, expires_in, user (PerfilUsuario).
        """
        if self._test_mode:
            return self._register_test(email, password, nombre, apellido, ocupacion, meta_sueno)

        # Producción: Supabase Auth maneja hash de contraseña (RNF01)
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
            })
        except Exception as exc:
            error_msg = str(exc).lower()
            if any(kw in error_msg for kw in ("already registered", "already been registered", "duplicate")):
                raise UserAlreadyExistsError() from exc
            raise

        if response.user is None:
            raise UserAlreadyExistsError()

        user_id = response.user.id
        profile = PerfilUsuario(
            id=user_id, email=email, nombre=nombre,
            apellido=apellido, ocupacion=ocupacion, meta_sueno=meta_sueno,
        )
        self.profile_repo.create(profile)

        session = response.session
        return {
            "access_token": session.access_token if session else "",
            "refresh_token": session.refresh_token if session else "",
            "token_type": "bearer",
            "expires_in": session.expires_in if session else 3600,
            "user": profile,
        }

    def login(self, email: str, password: str) -> dict:
        """Autentica un usuario con Supabase Auth (RF02, RNF02).

        Retorna dict con: access_token, refresh_token, token_type, expires_in, user (PerfilUsuario).
        """
        if self._test_mode:
            return self._login_test(email, password)

        # Producción: Supabase Auth valida contraseña y emite sesión con expiración (RNF02)
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
        except Exception as exc:
            raise AuthenticationError() from exc

        if response.user is None or response.session is None:
            raise AuthenticationError()

        user_id = response.user.id
        profile = self.profile_repo.get_by_id(user_id)
        if profile is None:
            raise AuthenticationError("Perfil de usuario no encontrado.")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in,
            "user": profile,
        }

    def get_user_id_from_token(self, token: str) -> str:
        """Valida un token de sesión y retorna el UUID del usuario (RNF02)."""
        if self._test_mode:
            user_id = self._test_tokens.get(token)
            if user_id is None:
                raise InvalidTokenError()
            return user_id

        # Producción: Supabase Auth valida JWT con expiración
        try:
            user_response = self.client.auth.get_user(token)
        except Exception as exc:
            raise InvalidTokenError() from exc

        if user_response is None or user_response.user is None:
            raise InvalidTokenError()

        return user_response.user.id

    def delete_user(self, user_id: str) -> None:
        """Elimina la cuenta del usuario en Supabase Auth y en cascada todos sus datos (RF10).

        Requiere clave service_role en el cliente Supabase para ejecutar auth.admin.delete_user.
        Al eliminarse en auth.users, PostgreSQL desencadena la eliminación en cascada
        sobre perfiles_usuario y registros_sueno gracias a ON DELETE CASCADE.
        """
        if self._test_mode:
            # Modo test en memoria
            self.profile_repo.delete(user_id)
            # Limpiar test users y tokens asociados
            user_email = None
            for email, data in self._test_users.items():
                if data["id"] == user_id:
                    user_email = email
                    break
            if user_email:
                del self._test_users[user_email]
            tokens_to_del = [t for t, uid in self._test_tokens.items() if uid == user_id]
            for t in tokens_to_del:
                del self._test_tokens[t]
            return

        # Producción con Supabase Client
        try:
            self.client.auth.admin.delete_user(user_id)
        except Exception as exc:
            # Fallback en caso de que las políticas RLS o supabase requieran borrar perfil primero
            self.profile_repo.delete(user_id)
            raise RuntimeError(f"Error al eliminar usuario en Supabase Auth: {exc}") from exc

    # --- Métodos internos para modo de pruebas ---

    def _register_test(
        self,
        email: str,
        password: str,
        nombre: str,
        apellido: str,
        ocupacion: str,
        meta_sueno: float,
    ) -> dict:
        """Registro en memoria para pruebas unitarias sin conexión a Supabase."""
        if email in self._test_users:
            raise UserAlreadyExistsError()

        user_id = str(uuid.uuid4())
        self._test_users[email] = {
            "id": user_id, "email": email, "password": password,
        }
        token = f"test-token-{user_id}"
        self._test_tokens[token] = user_id

        profile = PerfilUsuario(
            id=user_id, email=email, nombre=nombre,
            apellido=apellido, ocupacion=ocupacion, meta_sueno=meta_sueno,
        )
        self.profile_repo.create(profile)

        return {
            "access_token": token,
            "refresh_token": f"test-refresh-{user_id}",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": profile,
        }

    def _login_test(self, email: str, password: str) -> dict:
        """Login en memoria para pruebas unitarias sin conexión a Supabase."""
        user_data = self._test_users.get(email)
        if user_data is None or user_data["password"] != password:
            raise AuthenticationError()

        user_id = user_data["id"]
        token = f"test-token-{user_id}"
        self._test_tokens[token] = user_id

        profile = self.profile_repo.get_by_id(user_id)
        if profile is None:
            raise AuthenticationError()

        return {
            "access_token": token,
            "refresh_token": f"test-refresh-{user_id}",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": profile,
        }
