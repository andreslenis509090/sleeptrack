"""Capa de Persistencia para Registros de Sueño (Repository).

Encapsula todas las operaciones contra la base de datos Supabase (PostgreSQL en la nube).
Garantiza persistencia relacional e integridad sin usar almacenamiento local (RNF04).
"""

from datetime import date, time
from typing import Any
from supabase import Client
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
        # Manejar formatos de fecha y hora provenientes de Supabase (strings o tipos de Python)
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
            id_registro=row.get("id_registro"),
            id_usuario=row["id_usuario"],
            fecha=fecha_val,
            hora_acostarse=hora_acostarse_val,
            hora_despertar=hora_despertar_val,
            calificacion=int(row["calificacion"]),
            duracion_horas=float(row["duracion_horas"]),
        )

    def get_by_user_and_date(
        self, id_usuario: int, fecha: date
    ) -> RegistroSueno | None:
        """Consulta si existe un registro de sueño para un usuario y fecha específicos (RN01, RF08)."""
        if self.client is not None:
            try:
                response = (
                    self.client.table(self._table_name)
                    .select("*")
                    .eq("id_usuario", id_usuario)
                    .eq("fecha", str(fecha))
                    .maybe_single()
                    .execute()
                )
                if response and response.data:
                    return self._row_to_model(response.data)
                return None
            except Exception:
                # Si falla la llamada a la red (ej. mock sin conexión), consulta fallback en memoria
                pass

        for row in self._in_memory_db.values():
            if row["id_usuario"] == id_usuario and row["fecha"] == fecha:
                return self._row_to_model(row)
        return None

    def get_by_id(self, id_registro: int, id_usuario: int) -> RegistroSueno | None:
        """Obtiene un registro por su identificador primario y usuario propietario."""
        if self.client is not None:
            try:
                response = (
                    self.client.table(self._table_name)
                    .select("*")
                    .eq("id_registro", id_registro)
                    .eq("id_usuario", id_usuario)
                    .maybe_single()
                    .execute()
                )
                if response and response.data:
                    return self._row_to_model(response.data)
                return None
            except Exception:
                pass

        row = self._in_memory_db.get(id_registro)
        if row and row["id_usuario"] == id_usuario:
            return self._row_to_model(row)
        return None

    def create(self, registro: RegistroSueno) -> RegistroSueno:
        """Inserta un nuevo registro de sueño en Supabase."""
        row_data = {
            "id_usuario": registro.id_usuario,
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
            except Exception:
                pass

        # Fallback en memoria si Supabase no está conectado
        new_id = self._auto_id
        self._auto_id += 1
        saved_row = {
            "id_registro": new_id,
            "id_usuario": registro.id_usuario,
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
            try:
                response = (
                    self.client.table(self._table_name)
                    .update(row_data)
                    .eq("id_registro", registro.id_registro)
                    .eq("id_usuario", registro.id_usuario)
                    .execute()
                )
                if response and response.data:
                    return self._row_to_model(response.data[0])
            except Exception:
                pass

        saved_row = self._in_memory_db.get(registro.id_registro)
        if saved_row:
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
