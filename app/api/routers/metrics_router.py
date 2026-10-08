"""Router para el Módulo de Métricas Semanales (RF11-RF14, RN03, HU2).

Define endpoints para consulta y análisis de patrones de descanso semanal.
Sigue el patrón en tres capas: Router -> Service -> Repository.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user_id, get_metrics_service
from app.schemas.metrics import WeeklyMetricsResponse
from app.services.metrics_service import MetricsService

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


@router.get(
    "/weekly",
    response_model=WeeklyMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar métricas semanales de descanso (RF11-RF14, RN03, HU2)",
    responses={
        200: {"description": "Resumen semanal calculado dinámicamente con detección de días críticos."},
        401: {"description": "No autorizado. Token de sesión requerido."},
    },
)
def get_weekly_metrics(
    user_id: Annotated[str, Depends(get_current_user_id)],
    metrics_service: Annotated[MetricsService, Depends(get_metrics_service)],
    semana_inicio: Annotated[
        date | None,
        Query(
            alias="semana_inicio",
            description=(
                "Fecha de inicio de la semana en formato YYYY-MM-DD (debe corresponder a un Lunes). "
                "Permite navegar entre semanas anteriores (RF13). "
                "Si se omite, se calcula por defecto el Lunes de la semana actual según la fecha del servidor, "
                "por lo que se recomienda que el cliente envíe semana_inicio explícitamente."
            ),
        ),
    ] = None,
) -> WeeklyMetricsResponse:
    """Retorna el resumen semanal de 7 días (Lunes a Domingo) para el usuario autenticado:

    - **Horas por día y promedio semanal:** Calcula el promedio a 1 decimal sobre los días que tienen registro (RF11).
      Los días sin registro se muestran con `duracionHoras: null` y no afectan el promedio.
    - **Detección de días críticos (RN03, RF12):** Compara las horas dormidas contra la meta personal de sueño
      del perfil del usuario, o 6.0 horas por defecto si no tiene meta definida. Los días sin registro no se marcan como críticos.
    - **Navegación histórica (RF13):** Admite semanas anteriores pasando `semana_inicio`.
    - **Datos insuficientes (RF14):** Si no existen registros en la semana, responde con `datosSuficientes: false`
      y mensaje descriptivo.
    - **Aislamiento:** El cálculo se realiza dinámicamente sobre `registros_sueno` filtrando exclusivamente por el usuario autenticado.
    """
    return metrics_service.get_weekly_metrics(
        id_usuario=user_id,
        semana_inicio=semana_inicio,
    )
