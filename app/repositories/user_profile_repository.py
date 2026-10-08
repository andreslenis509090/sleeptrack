"""Capa de Persistencia para Perfiles de Usuario (Repository).

Encapsula operaciones CRUD sobre la tabla perfiles_usuario en Supabase (PostgreSQL en la nube).
La tabla almacena los datos de perfil (RF01) vinculados al UUID de auth.users.
Las contraseñas NO se almacenan aquí — las gestiona Supabase Auth (RNF01).
"""

from typing import Any

from supabase import Client

from app.models.user_profile import PerfilUsuario


class UserProfileRepository:
    """Repositorio para la entidad PerfilUsuario."""

    def __init__(self, client: Client | None = None) -> None:
        self.client = client
        self._table_name = "perfiles_usuario"
        # Almacenamiento fallback en memoria para pruebas sin conexión a Supabase
        self._in_memory_db: dict[str, dict[str, Any]] = {}

    def _row_to_model(self, row: dict[str, Any]) -> PerfilUsuario:
        """Convierte una fila de Supabase a entidad de dominio PerfilUsuario."""
        return PerfilUsuario(
            id=str(row["id"]),
            email=str(row["email"]),
            nombre=str(row["nombre"]),
            apellido=str(row["apellido"]),
            ocupacion=str(row["ocupacion"]),
            meta_sueno=float(row["meta_sueno"]),
        )

    def create(self, profile: PerfilUsuario) -> PerfilUsuario:
        """Inserta un nuevo perfil de usuario en Supabase (RF01)."""
        row_data = {
            "id": profile.id,
            "email": profile.email,
            "nombre": profile.nombre,
            "apellido": profile.apellido,
            "ocupacion": profile.ocupacion,
            "meta_sueno": profile.meta_sueno,
        }

        if self.client is not None:
            response = (
                self.client.table(self._table_name).insert(row_data).execute()
            )
            if response and response.data:
                return self._row_to_model(response.data[0])
            raise RuntimeError("No se recibieron datos de confirmación tras insertar perfil en Supabase.")

        # Fallback en memoria para tests
        self._in_memory_db[profile.id] = row_data.copy()
        return self._row_to_model(row_data)

    def get_by_id(self, user_id: str) -> PerfilUsuario | None:
        """Obtiene un perfil por el UUID del usuario de Supabase Auth."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .select("*")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            if response and response.data:
                return self._row_to_model(response.data)
            return None

        row = self._in_memory_db.get(user_id)
        if row:
            return self._row_to_model(row)
        return None

    def update(self, profile: PerfilUsuario) -> PerfilUsuario:
        """Actualiza los datos de perfil de un usuario existente."""
        row_data = {
            "nombre": profile.nombre,
            "apellido": profile.apellido,
            "ocupacion": profile.ocupacion,
            "meta_sueno": profile.meta_sueno,
        }

        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .update(row_data)
                .eq("id", profile.id)
                .execute()
            )
            if response and response.data:
                return self._row_to_model(response.data[0])
            raise ValueError(f"Perfil {profile.id} no encontrado en Supabase para actualizar.")

        if profile.id in self._in_memory_db:
            self._in_memory_db[profile.id].update(row_data)
            return self._row_to_model(self._in_memory_db[profile.id])
        raise ValueError(f"Perfil {profile.id} no encontrado para actualizar.")

    def delete(self, user_id: str) -> bool:
        """Elimina el perfil de un usuario (RF10)."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .delete()
                .eq("id", user_id)
                .execute()
            )
            return bool(response and response.data)

        if user_id in self._in_memory_db:
            del self._in_memory_db[user_id]
            return True
        return False
