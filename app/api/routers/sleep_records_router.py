"""Router para el Módulo de Registro de Sueño (HU1: RF03-RF09, RN01, RN02).

Define los endpoints HTTP y mapea las excepciones de dominio a códigos de respuesta estándar.
No contiene lógica de negocio ni interactúa directamente con la persistencia.
"""

from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_current_user_id, get_sleep_record_service
from app.core.exceptions import (
    FutureSleepTimeError,
    InvalidSleepDataError,
    SleepRecordAlreadyExistsError,
    SleepRecordNotFoundError,
)
from app.schemas.sleep_record import (
    SleepRecordConflictResponse,
    SleepRecordCreate,
    SleepRecordResponse,
    SleepRecordUpdate,
)
from app.services.sleep_record_service import SleepRecordService

router = APIRouter(
    prefix="/sleep-records",
    tags=["Sleep Records"],
)


@router.post(
    "",
    response_model=SleepRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro diario de sueño (RF03, RF04, RF05, RF06, RN01, RN02)",
    responses={
        201: {"description": "Registro creado exitosamente y duración calculada."},
        400: {"description": "Hora de inicio futura (RN02) o datos inválidos."},
        409: {
            "model": SleepRecordConflictResponse,
            "description": "Ya existe un registro para esta fecha (RN01 / RF08).",
        },
        422: {"description": "Error de validación en esquema o tipos."},
    },
)
def create_sleep_record(
    payload: SleepRecordCreate,
    service: Annotated[SleepRecordService, Depends(get_sleep_record_service)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SleepRecordResponse:
    """Crea un registro de sueño diario.

    - RF03: Registra horaAcostarse, horaDespertar, fecha y calificacion (1-5).
    - RF04: Calcula automáticamente la duración total considerando cruce de medianoche.
    - RF05 / RN02: Valida que la hora de inicio no sea futura contra el reloj en tiempo real.
    - RF06: Valida campos y formatos de hora.
    - RN01 / RF08: Si ya existe un registro en la fecha, bloquea y retorna 409 con el ID existente.
    """
    try:
        registro = service.create_sleep_record(id_usuario=user_id, data=payload)
        return SleepRecordResponse(
            id_registro=registro.id_registro or 0,
            id_usuario=registro.id_usuario,
            fecha=registro.fecha,
            hora_acostarse=registro.hora_acostarse,
            hora_despertar=registro.hora_despertar,
            calificacion=registro.calificacion,
            duracion_horas=registro.duracion_horas,
            mensaje="Registro de descanso guardado exitosamente (RF08).",
        )
    except SleepRecordAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": exc.message,
                "code": exc.code,
                "existing_record_id": exc.existing_record_id,
            },
        ) from exc
    except FutureSleepTimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
    except InvalidSleepDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": exc.message,
                "code": exc.code,
                "field": exc.field,
            },
        ) from exc


@router.get(
    "/by-date/{fecha}",
    response_model=SleepRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar registro de sueño por fecha (RF08, RN01)",
    responses={
        200: {"description": "Registro encontrado para la fecha especificada."},
        404: {"description": "No existe registro para la fecha indicada."},
    },
)
def get_sleep_record_by_date(
    fecha: date,
    service: Annotated[SleepRecordService, Depends(get_sleep_record_service)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SleepRecordResponse:
    """Permite al cliente móvil consultar si ya existe un registro para una fecha específica (RF08, RN01).

    Facilita que la interfaz ofrezca editar en lugar de crear un duplicado antes de enviar el formulario.
    """
    registro = service.get_sleep_record_by_date(id_usuario=user_id, fecha=fecha)
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"No existe registro de sueño para la fecha {fecha}.",
                "code": "RECORD_NOT_FOUND",
            },
        )
    return SleepRecordResponse(
        id_registro=registro.id_registro or 0,
        id_usuario=registro.id_usuario,
        fecha=registro.fecha,
        hora_acostarse=registro.hora_acostarse,
        hora_despertar=registro.hora_despertar,
        calificacion=registro.calificacion,
        duracion_horas=registro.duracion_horas,
    )


@router.put(
    "/{id_registro}",
    response_model=SleepRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Editar un registro de sueño existente (RF08, RF04, RN02)",
    responses={
        200: {"description": "Registro de sueño editado exitosamente."},
        400: {"description": "Hora futura o datos inválidos."},
        404: {"description": "Registro no encontrado."},
    },
)
def update_sleep_record(
    id_registro: int,
    payload: SleepRecordUpdate,
    service: Annotated[SleepRecordService, Depends(get_sleep_record_service)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SleepRecordResponse:
    """Edita un registro existente para una fecha determinada (RF08).

    Recalcula automáticamente la duración total (RF04) y valida que la hora no sea futura (RN02).
    """
    try:
        registro_actualizado = service.update_sleep_record(
            id_registro=id_registro,
            id_usuario=user_id,
            data=payload,
        )
        return SleepRecordResponse(
            id_registro=registro_actualizado.id_registro or id_registro,
            id_usuario=registro_actualizado.id_usuario,
            fecha=registro_actualizado.fecha,
            hora_acostarse=registro_actualizado.hora_acostarse,
            hora_despertar=registro_actualizado.hora_despertar,
            calificacion=registro_actualizado.calificacion,
            duracion_horas=registro_actualizado.duracion_horas,
            mensaje="Registro de descanso actualizado exitosamente (RF08).",
        )
    except SleepRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
    except FutureSleepTimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
    except InvalidSleepDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": exc.message,
                "code": exc.code,
                "field": exc.field,
            },
        ) from exc
