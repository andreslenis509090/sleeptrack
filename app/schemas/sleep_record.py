"""Esquemas Pydantic v2 para la validación y serialización de registros de sueño.

Cumple con RF03, RF04, RF05, RF06 y RF08.
Permite tanto nomenclatura snake_case como camelCase para interoperabilidad móvil.
"""

from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field


class SleepRecordCreate(BaseModel):
    """Esquema para crear un registro diario de sueño (RF03, RF06)."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "fecha": "2026-10-07",
                "horaAcostarse": "23:00",
                "horaDespertar": "07:00",
                "calificacion": 4,
            }
        },
    )

    fecha: date = Field(
        ...,
        description="Fecha del evento de descanso (YYYY-MM-DD)",
    )
    hora_acostarse: time = Field(
        ...,
        alias="horaAcostarse",
        description="Hora de inicio de sueño (HH:MM o HH:MM:SS)",
    )
    hora_despertar: time = Field(
        ...,
        alias="horaDespertar",
        description="Hora de despertar (HH:MM o HH:MM:SS)",
    )
    calificacion: int = Field(
        ...,
        ge=1,
        le=5,
        description="Autopercepción del descanso en escala de 1 a 5 (RF05/RF03)",
    )


class SleepRecordUpdate(BaseModel):
    """Esquema para editar un registro de sueño existente (RF08)."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "horaAcostarse": "23:30",
                "horaDespertar": "07:15",
                "calificacion": 5,
            }
        },
    )

    hora_acostarse: time = Field(
        ...,
        alias="horaAcostarse",
        description="Nueva hora de inicio de sueño",
    )
    hora_despertar: time = Field(
        ...,
        alias="horaDespertar",
        description="Nueva hora de despertar",
    )
    calificacion: int = Field(
        ...,
        ge=1,
        le=5,
        description="Nueva autopercepción del descanso en escala de 1 a 5",
    )


class SleepRecordResponse(BaseModel):
    """Esquema de respuesta de un registro de sueño persistido (RF04, RF08)."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    id_registro: int = Field(..., alias="idRegistro")
    id_usuario: int = Field(..., alias="idUsuario")
    fecha: date
    hora_acostarse: time = Field(..., alias="horaAcostarse")
    hora_despertar: time = Field(..., alias="horaDespertar")
    calificacion: int
    duracion_horas: float = Field(
        ...,
        alias="duracionHoras",
        description="Duración calculada automáticamente cruzando medianoche (RF04)",
    )
    mensaje: str | None = Field(
        default=None,
        description="Mensaje de confirmación inmediata (RF08)",
    )


class SleepRecordConflictResponse(BaseModel):
    """Esquema para el error 409 Conflict cuando ya existe un registro en la fecha (RN01, RF08)."""

    detail: str = Field(
        default="Ya existe un registro de sueño para esta fecha. Utilice la opción de edición (RF08)."
    )
    code: str = Field(default="RECORD_ALREADY_EXISTS")
    existing_record_id: int | None = Field(
        default=None,
        alias="existingRecordId",
        description="ID del registro previo para habilitar la edición directa",
    )


class ErrorDetail(BaseModel):
    """Detalle individual de un error estandarizado."""

    code: str
    message: str
    field: str | None = None


class StandardErrorResponse(BaseModel):
    """Esquema de respuesta de error estandarizado según la especificación de api-backend."""

    error: ErrorDetail
