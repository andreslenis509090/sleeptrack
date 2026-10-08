"""Capa de Persistencia para Registros de Sueño (Repository).

Encapsula todas las operaciones contra la base de datos Supabase (PostgreSQL en la nube).
Garantiza persistencia relacional e integridad sin usar almacenamiento local (RNF04).
Gestiona las restricciones del esquema relacional, incluyendo la restricción
única usuario+fecha para RN01 (uq_registros_sueno_usuario_fecha).
"""

from datetime import date, time
from typing import Any
from postgrest.exceptions import APIError
from supabase import Client
from app.core.exceptions import SleepRecordAlreadyExistsError
from app.models.sleep_record import RegistroSueno


class SleepRecordRepository:
    """Repositorio para la entidad RegistroSueno."""

    def __init__(self, client: Client | None = None) -> None:
        self.client = client
        self._table_name = "registros_sueno"
        # Almacenamiento fallback en memoria para pruebas si no hay cliente conectado
        self._in_memory_db: dict[int, dict[str, Any]] = {}
        self._auto_id: int = 1

    def _row_to_model(self, row: dict[str, Any]) -> RegistroSueno:
        """Convierte una fila de la base de datos Supabase a una entidad de dominio RegistroSueno."""
        fecha_val = row["fecha"]
        if isinstance(fecha_val, str):
            fecha_val = date.fromisoformat(fecha_val)

        hora_acostarse_val = row["hora_acostarse"]
        if isinstance(hora_acostarse_val, str):
            hora_acostarse_val = time.fromisoformat(hora_acostarse_val)

        hora_despertar_val = row["hora_despertar"]
        if isinstance(hora_despertar_val, str):
            hora_despertar_val = time.fromisoformat(hora_despertar_val)

        return RegistroSueno(
            id_registro=int(row["id_registro"]) if row.get("id_registro") is not None else None,
            id_usuario=str(row["id_usuario"]),
            fecha=fecha_val,
            hora_acostarse=hora_acostarse_val,
            hora_despertar=hora_despertar_val,
            calificacion=int(row["calificacion"]),
            duracion_horas=float(row["duracion_horas"]),
        )

    def get_by_user_and_date(
        self, id_usuario: str, fecha: date
    ) -> RegistroSueno | None:
        """Consulta si existe un registro de sueño para un usuario y fecha específicos (RN01, RF08)."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .select("*")
                .eq("id_usuario", str(id_usuario))
                .eq("fecha", str(fecha))
                .maybe_single()
                .execute()
            )
            if response and response.data:
                return self._row_to_model(response.data)
            return None

        # Fallback en memoria para tests aislados
        for row in self._in_memory_db.values():
            if str(row["id_usuario"]) == str(id_usuario) and row["fecha"] == fecha:
                return self._row_to_model(row)
        return None

    def get_by_id(self, id_registro: int, id_usuario: str) -> RegistroSueno | None:
        """Obtiene un registro por su identificador primario y usuario propietario."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .select("*")
                .eq("id_registro", id_registro)
                .eq("id_usuario", str(id_usuario))
                .maybe_single()
                .execute()
            )
            if response and response.data:
                return self._row_to_model(response.data)
            return None

        row = self._in_memory_db.get(id_registro)
        if row and str(row["id_usuario"]) == str(id_usuario):
            return self._row_to_model(row)
        return None

    def create(self, registro: RegistroSueno) -> RegistroSueno:
        """Inserta un nuevo registro de sueño en Supabase aplicando la restricción única de RN01."""
        row_data = {
            "id_usuario": str(registro.id_usuario),
            "fecha": str(registro.fecha),
            "hora_acostarse": str(registro.hora_acostarse),
            "hora_despertar": str(registro.hora_despertar),
            "calificacion": registro.calificacion,
            "duracion_horas": registro.duracion_horas,
        }

        if self.client is not None:
            try:
                response = (
                    self.client.table(self._table_name).insert(row_data).execute()
                )
                if response and response.data:
                    return self._row_to_model(response.data[0])
                raise RuntimeError("No se recibieron datos de confirmación tras la inserción en Supabase.")
            except APIError as exc:
                # Código PostgreSQL 23505 = unique_violation (violación de uq_registros_sueno_usuario_fecha)
                if exc.code == "23505" or "unique constraint" in (exc.message or "").lower():
                    existente = self.get_by_user_and_date(registro.id_usuario, registro.fecha)
                    existing_id = existente.id_registro if existente else None
                    raise SleepRecordAlreadyExistsError(
                        message="Ya existe un registro de sueño para esta fecha. Utilice la opción de edición (RF08).",
                        existing_record_id=existing_id,
                    ) from exc
                raise

        # Fallback en memoria si no hay cliente conectado
        new_id = self._auto_id
        self._auto_id += 1
        saved_row = {
            "id_registro": new_id,
            "id_usuario": str(registro.id_usuario),
            "fecha": registro.fecha,
            "hora_acostarse": registro.hora_acostarse,
            "hora_despertar": registro.hora_despertar,
            "calificacion": registro.calificacion,
            "duracion_horas": registro.duracion_horas,
        }
        self._in_memory_db[new_id] = saved_row
        return self._row_to_model(saved_row)

    def update(self, registro: RegistroSueno) -> RegistroSueno:
        """Actualiza un registro de sueño existente en Supabase (RF08)."""
        if registro.id_registro is None:
            raise ValueError("No se puede actualizar un registro sin id_registro")

        row_data = {
            "hora_acostarse": str(registro.hora_acostarse),
            "hora_despertar": str(registro.hora_despertar),
            "calificacion": registro.calificacion,
            "duracion_horas": registro.duracion_horas,
        }

        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .update(row_data)
                .eq("id_registro", registro.id_registro)
                .eq("id_usuario", str(registro.id_usuario))
                .execute()
            )
            if response and response.data:
                return self._row_to_model(response.data[0])
            raise ValueError(f"Registro {registro.id_registro} no encontrado en Supabase para actualizar.")

        saved_row = self._in_memory_db.get(registro.id_registro)
        if saved_row and str(saved_row["id_usuario"]) == str(registro.id_usuario):
            saved_row.update(
                {
                    "hora_acostarse": registro.hora_acostarse,
                    "hora_despertar": registro.hora_despertar,
                    "calificacion": registro.calificacion,
                    "duracion_horas": registro.duracion_horas,
                }
            )
            return self._row_to_model(saved_row)

        raise ValueError(f"Registro {registro.id_registro} no encontrado para actualizar.")

    def delete(self, id_registro: int, id_usuario: str) -> bool:
        """Elimina un registro de sueño propio del usuario (RF09)."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .delete()
                .eq("id_registro", id_registro)
                .eq("id_usuario", str(id_usuario))
                .execute()
            )
            return bool(response and response.data)

        if id_registro in self._in_memory_db:
            if str(self._in_memory_db[id_registro]["id_usuario"]) == str(id_usuario):
                del self._in_memory_db[id_registro]
                return True
        return False

    def list_by_user(self, id_usuario: str) -> list[RegistroSueno]:
        """Lista todos los registros de sueño de un usuario ordenados por fecha descendente (RF03, RNF08)."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .select("*")
                .eq("id_usuario", str(id_usuario))
                .order("fecha", desc=True)
                .execute()
            )
            if response and response.data:
                return [self._row_to_model(row) for row in response.data]
            return []

        return [
            self._row_to_model(row)
            for row in sorted(
                self._in_memory_db.values(),
                key=lambda r: r["fecha"],
                reverse=True,
            )
            if str(row["id_usuario"]) == str(id_usuario)
        ]

    def get_by_date_range(
        self, id_usuario: str, fecha_inicio: date, fecha_fin: date
    ) -> list[RegistroSueno]:
        """Obtiene los registros de un usuario comprendidos en un rango de fechas [inicio, fin] (RF11, RF13)."""
        if self.client is not None:
            response = (
                self.client.table(self._table_name)
                .select("*")
                .eq("id_usuario", str(id_usuario))
                .gte("fecha", str(fecha_inicio))
                .lte("fecha", str(fecha_fin))
                .order("fecha", desc=False)
                .execute()
            )
            if response and response.data:
                return [self._row_to_model(row) for row in response.data]
            return []

        # Fallback en memoria para tests
        registros = []
        for row in self._in_memory_db.values():
            if str(row["id_usuario"]) == str(id_usuario):
                fecha_val = row["fecha"]
                if isinstance(fecha_val, str):
                    fecha_val = date.fromisoformat(fecha_val)
                if fecha_inicio <= fecha_val <= fecha_fin:
                    registros.append(self._row_to_model(row))
        return sorted(registros, key=lambda r: r.fecha)
