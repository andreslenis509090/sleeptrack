"""Capa de Servicio para la Lógica de Negocio de Registros de Sueño.

Aplica estrictamente las reglas de negocio del dominio:
- RN01: Unicidad de 1 registro por usuario y fecha (RF08).
- RN02: Validación de hora de inicio de sueño no futura contra reloj en tiempo real (RF05).
- RF04: Cálculo automático de duración de sueño cruzando medianoche.
- RF06: Validación de campos obligatorios y formato.
- RF08: Edición de registro existente para la fecha en lugar de duplicar.

No contiene referencias a frameworks web (Request, Response, HTTPException)
y lanza únicamente excepciones de dominio tipadas.
"""

from datetime import date, datetime
from app.core.exceptions import (
    FutureSleepTimeError,
    InvalidSleepDataError,
    SleepRecordAlreadyExistsError,
    SleepRecordNotFoundError,
)
from app.models.sleep_record import RegistroSueno
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.schemas.sleep_record import SleepRecordCreate, SleepRecordUpdate


class SleepRecordService:
    """Servicio que encapsula las reglas de negocio y casos de uso para registros de sueño."""

    def __init__(self, repository: SleepRecordRepository) -> None:
        self.repository = repository

    def create_sleep_record(
        self,
        id_usuario: str,
        data: SleepRecordCreate,
        now: datetime | None = None,
    ) -> RegistroSueno:
        """Crea un nuevo registro diario de sueño aplicando RN01 y RN02 (RF03-RF08).

        1. RN01: Valida que no exista registro previo para el usuario y la fecha.
           Si ya existe, lanza SleepRecordAlreadyExistsError (RF08).
        2. RN02 / RF05: Valida que la hora de acostarse no sea futura.
        3. RF04: Calcula automáticamente la duración de horas cruzando medianoche.
        4. Persiste en el repositorio de Supabase y retorna la entidad.
        """
        # RN01: Unicidad por usuario y fecha
        registro_existente = self.repository.get_by_user_and_date(
            id_usuario=id_usuario, fecha=data.fecha
        )
        if registro_existente is not None:
            raise SleepRecordAlreadyExistsError(
                message="Ya existe un registro de sueño para esta fecha. Utilice la opción de edición (RF08).",
                existing_record_id=registro_existente.id_registro,
            )

        # RN02 y RF05: Validar que hora de inicio no sea futura
        RegistroSueno.validar_hora_futura(
            fecha=data.fecha,
            hora_acostarse=data.hora_acostarse,
            now=now,
        )

        # RF06: Validación de calificación dentro del rango 1-5
        if not (1 <= data.calificacion <= 5):
            raise InvalidSleepDataError(
                "La calificación debe estar entre 1 y 5.",
                field="calificacion",
            )

        # RF04: Cálculo automático de duración
        duracion_horas = RegistroSueno.calcular_duracion(
            hora_acostarse=data.hora_acostarse,
            hora_despertar=data.hora_despertar,
        )

        nuevo_registro = RegistroSueno(
            id_registro=None,
            id_usuario=id_usuario,
            fecha=data.fecha,
            hora_acostarse=data.hora_acostarse,
            hora_despertar=data.hora_despertar,
            calificacion=data.calificacion,
            duracion_horas=duracion_horas,
        )

        return self.repository.create(nuevo_registro)

    def update_sleep_record(
        self,
        id_registro: int,
        id_usuario: str,
        data: SleepRecordUpdate,
        now: datetime | None = None,
    ) -> RegistroSueno:
        """Edita un registro de sueño existente para una fecha determinada (RF08).

        Recalcula la duración (RF04) y valida que la nueva hora de acostarse no sea futura (RN02).
        """
        registro = self.repository.get_by_id(
            id_registro=id_registro, id_usuario=id_usuario
        )
        if registro is None:
            raise SleepRecordNotFoundError(
                f"No se encontró el registro de sueño con ID {id_registro}."
            )

        # RN02 / RF05: Validar hora no futura para la fecha del registro existente
        RegistroSueno.validar_hora_futura(
            fecha=registro.fecha,
            hora_acostarse=data.hora_acostarse,
            now=now,
        )

        # RF06: Validar rango de calificación
        if not (1 <= data.calificacion <= 5):
            raise InvalidSleepDataError(
                "La calificación debe estar entre 1 y 5.",
                field="calificacion",
            )

        # RF04: Recalcular duración cruzando medianoche
        duracion_horas = RegistroSueno.calcular_duracion(
            hora_acostarse=data.hora_acostarse,
            hora_despertar=data.hora_despertar,
        )

        registro.hora_acostarse = data.hora_acostarse
        registro.hora_despertar = data.hora_despertar
        registro.calificacion = data.calificacion
        registro.duracion_horas = duracion_horas

        return self.repository.update(registro)

    def get_sleep_record_by_date(
        self, id_usuario: str, fecha: date
    ) -> RegistroSueno | None:
        """Consulta si existe un registro en una fecha específica (RF08, RN01)."""
        return self.repository.get_by_user_and_date(
            id_usuario=id_usuario, fecha=fecha
        )

    def get_sleep_record_by_id(
        self, id_registro: int, id_usuario: str
    ) -> RegistroSueno:
        """Obtiene un registro por ID o lanza SleepRecordNotFoundError."""
        registro = self.repository.get_by_id(
            id_registro=id_registro, id_usuario=id_usuario
        )
        if registro is None:
            raise SleepRecordNotFoundError(
                f"No se encontró el registro de sueño con ID {id_registro}."
            )
        return registro
