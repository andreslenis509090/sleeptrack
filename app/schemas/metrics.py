"""Esquemas Pydantic v2 para el Módulo de Métricas Semanales (RF11-RF14, RN03).

Soporta interoperabilidad snake_case y camelCase para el cliente móvil.
"""

from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class DiaMetricaResponse(BaseModel):
    """Representación del resumen diario de una semana (RF11, RF12, RN03)."""

    model_config = ConfigDict(populate_by_name=True)

    fecha: date
    dia_semana: str = Field(..., alias="diaSemana", description="Nombre del día en español (ej. Lunes)")
    duracion_horas: float | None = Field(
        default=None,
        alias="duracionHoras",
        description="Horas dormidas calculadas; null si no hubo registro ese día",
    )
    es_critico: bool = Field(
        default=False,
        alias="esCritico",
        description="True si se registró descanso menor a la meta de sueño o 6h (RN03)",
    )


class WeeklyMetricsResponse(BaseModel):
    """Resumen semanal de horas dormidas y análisis de días críticos (RF11-RF14, RN03)."""

    model_config = ConfigDict(populate_by_name=True)

    semana_inicio: date = Field(..., alias="semanaInicio", description="Fecha de inicio (Lunes)")
    semana_fin: date = Field(..., alias="semanaFin", description="Fecha de fin (Domingo)")
    promedio_horas: float | None = Field(
        default=None,
        alias="promedioHoras",
        description="Promedio semanal calculado a 1 decimal sobre los días con registro (RF11)",
    )
    meta_sueno_aplicada: float = Field(
        ...,
        alias="metaSuenoAplicada",
        description="Meta personal de sueño o 6.0h por defecto si no tiene meta (RN03)",
    )
    dias_criticos: list[date] = Field(
        default_factory=list,
        alias="diasCriticos",
        description="Fechas identificadas como días críticos (RF12, RN03)",
    )
    dias: list[DiaMetricaResponse] = Field(
        ...,
        description="Lista de los 7 días de la semana con sus métricas diarias proyectadas",
    )
    datos_suficientes: bool = Field(
        ...,
        alias="datosSuficientes",
        description="False si la semana no cuenta con registros de descanso (RF14)",
    )
    mensaje: str = Field(
        ...,
        description="Mensaje informativo para el usuario",
    )
