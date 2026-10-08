"""Capa de Servicio para el Módulo de Métricas Semanales (RF11-RF14, RN03).

Aplica estrictamente las reglas de negocio del dominio:
- RF11: Cálculo de horas por día y promedio semanal redondeado a 1 decimal
        (calculado exclusivamente sobre los días que tienen registro).
- RF12 / RN03: Detección de días críticos comparando horas dormidas contra
               la meta de sueño del perfil, o 6.0 horas si el usuario no tiene meta.
               Los días sin registro NO son críticos y tienen duracionHoras = None.
- RF13: Permite consultar semanas anteriores mediante semana_inicio explícita.
- RF14: Respuesta clara si no hay datos suficientes (0 registros en la semana).
- Cálculo dinámico directo sobre registros_sueno (sin tabla metrica_semanal).
- La semana inicia en Lunes y termina en Domingo (7 días calendario).
"""

from datetime import date, timedelta

from app.models.sleep_record import RegistroSueno
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.metrics import DiaMetricaResponse, WeeklyMetricsResponse

NOMBRES_DIAS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


class MetricsService:
    """Servicio que encapsula la lógica de cálculo dinámico de métricas semanales."""

    def __init__(
        self,
        sleep_repo: SleepRecordRepository,
        profile_repo: UserProfileRepository,
    ) -> None:
        self.sleep_repo = sleep_repo
        self.profile_repo = profile_repo

    def get_weekly_metrics(
        self,
        id_usuario: str,
        semana_inicio: date | None = None,
        hoy: date | None = None,
    ) -> WeeklyMetricsResponse:
        """Calcula dinámicamente las métricas semanales para un usuario (RF11-RF14, RN03).

        - Si semana_inicio es None, se calcula el lunes de la semana actual basado en la
          fecha del servidor (o parámetro `hoy`). Se documenta que el cliente debe enviar
          semana_inicio explícitamente para controlar la semana deseada.
        - Los turnos que cruzan la medianoche se contabilizan en la fecha en que el usuario se acostó.
        """
        # 1. Determinar semana_inicio (Lunes) y semana_fin (Domingo)
        if semana_inicio is None:
            referencia = hoy or date.today()
            # Lunes de la semana actual (weekday 0 = lunes)
            semana_inicio = referencia - timedelta(days=referencia.weekday())

        semana_fin = semana_inicio + timedelta(days=6)

        # 2. Consultar perfil del usuario para obtener meta_sueno (RN03)
        perfil = self.profile_repo.get_by_id(id_usuario)
        meta_aplicada = (
            float(perfil.meta_sueno)
            if perfil is not None and perfil.meta_sueno is not None
            else 6.0
        )

        # 3. Obtener registros de sueño en el rango [semana_inicio, semana_fin]
        registros = self.sleep_repo.get_by_date_range(
            id_usuario=id_usuario,
            fecha_inicio=semana_inicio,
            fecha_fin=semana_fin,
        )

        # Indexar registros por fecha
        registros_por_fecha: dict[date, RegistroSueno] = {
            r.fecha: r for r in registros
        }

        # 4. Proyectar los 7 días de la semana (Lunes a Domingo)
        dias_response: list[DiaMetricaResponse] = []
        dias_criticos: list[date] = []
        duraciones_registradas: list[float] = []

        for offset in range(7):
            fecha_dia = semana_inicio + timedelta(days=offset)
            nombre_dia = NOMBRES_DIAS[offset]
            reg = registros_por_fecha.get(fecha_dia)

            if reg is not None:
                duracion = reg.duracion_horas
                duraciones_registradas.append(duracion)
                # RN03: Crítico si horas dormidas < meta_aplicada
                es_critico = duracion < meta_aplicada
                if es_critico:
                    dias_criticos.append(fecha_dia)
                dias_response.append(
                    DiaMetricaResponse(
                        fecha=fecha_dia,
                        dia_semana=nombre_dia,
                        duracion_horas=duracion,
                        es_critico=es_critico,
                    )
                )
            else:
                # Día sin registro: duracionHoras = None, no es crítico
                dias_response.append(
                    DiaMetricaResponse(
                        fecha=fecha_dia,
                        dia_semana=nombre_dia,
                        duracion_horas=None,
                        es_critico=False,
                    )
                )

        # 5. Calcular promedio semanal y datos suficientes (RF11, RF14)
        if not duraciones_registradas:
            # RF14: No hay registros en toda la semana
            return WeeklyMetricsResponse(
                semana_inicio=semana_inicio,
                semana_fin=semana_fin,
                promedio_horas=None,
                meta_sueno_aplicada=meta_aplicada,
                dias_criticos=[],
                dias=dias_response,
                datos_suficientes=False,
                mensaje="No se encontraron registros de sueño para la semana seleccionada (RF14).",
            )

        # RF11: Promedio con 1 decimal sobre los días que tienen registro
        promedio = round(sum(duraciones_registradas) / len(duraciones_registradas), 1)

        mensaje = (
            f"Se analizaron {len(duraciones_registradas)} días con registro. "
            f"Promedio semanal: {promedio} horas. "
            f"Días críticos detectados: {len(dias_criticos)}."
        )

        return WeeklyMetricsResponse(
            semana_inicio=semana_inicio,
            semana_fin=semana_fin,
            promedio_horas=promedio,
            meta_sueno_aplicada=meta_aplicada,
            dias_criticos=dias_criticos,
            dias=dias_response,
            datos_suficientes=True,
            mensaje=mensaje,
        )
