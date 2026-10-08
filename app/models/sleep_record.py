"""Modelo de Dominio para Registro de Sueño (HU1, RF03-RF09).

Representa un evento diario de descanso ingresado manualmente por el usuario.
No utiliza sensores automáticos ni modelos de inteligencia artificial.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from app.core.exceptions import FutureSleepTimeError, InvalidSleepDataError


@dataclass
class RegistroSueno:
    """Entidad de dominio RegistroSueno según especificación del informe técnico."""

    id_registro: int | None
    id_usuario: int
    fecha: date
    hora_acostarse: time
    hora_despertar: time
    calificacion: int
    duracion_horas: float

    @staticmethod
    def calcular_duracion(hora_acostarse: time, hora_despertar: time) -> float:
        """Calcula la duración en horas soportando el cruce de medianoche (RF04).

        Si hora_despertar <= hora_acostarse, el descanso cruzó la medianoche,
        por lo que se suma un día completo (24 horas) al cálculo.
        Retorna la duración redondeada a 2 decimales.
        """
        inicio = datetime.combine(date.min, hora_acostarse)
        fin = datetime.combine(date.min, hora_despertar)

        if fin <= inicio:
            # El sueño cruzó la medianoche
            fin += timedelta(days=1)

        segundos = (fin - inicio).total_seconds()
        return round(segundos / 3600.0, 2)

    @staticmethod
    def validar_hora_futura(
        fecha: date,
        hora_acostarse: time,
        now: datetime | None = None,
    ) -> bool:
        """Valida que la hora de inicio de sueño no corresponda al futuro (RF05, RN02).

        Compara la combinación de fecha y hora_acostarse contra el reloj en tiempo real.
        Lanza FutureSleepTimeError si es posterior al momento actual.
        """
        current = now or datetime.now()
        inicio_dt = datetime.combine(fecha, hora_acostarse)

        # Normalizar zonas horarias si una es consciente y la otra ingenua
        if current.tzinfo is not None and inicio_dt.tzinfo is None:
            inicio_dt = inicio_dt.replace(tzinfo=current.tzinfo)
        elif current.tzinfo is None and inicio_dt.tzinfo is not None:
            current = current.replace(tzinfo=inicio_dt.tzinfo)

        if inicio_dt > current:
            raise FutureSleepTimeError(
                "No se puede registrar una hora de inicio de sueño en el futuro."
            )
        return True

    @classmethod
    def crear(
        cls,
        id_usuario: int,
        fecha: date,
        hora_acostarse: time,
        hora_despertar: time,
        calificacion: int,
        now: datetime | None = None,
        id_registro: int | None = None,
    ) -> "RegistroSueno":
        """Factory method que aplica las validaciones del dominio al instanciar."""
        if not (1 <= calificacion <= 5):
            raise InvalidSleepDataError(
                "La calificación debe ser un valor entero entre 1 y 5.",
                field="calificacion",
            )

        # Validar RN02
        cls.validar_hora_futura(fecha, hora_acostarse, now=now)

        # Calcular RF04
        duracion = cls.calcular_duracion(hora_acostarse, hora_despertar)

        return cls(
            id_registro=id_registro,
            id_usuario=id_usuario,
            fecha=fecha,
            hora_acostarse=hora_acostarse,
            hora_despertar=hora_despertar,
            calificacion=calificacion,
            duracion_horas=duracion,
        )
