"""Pruebas para el Módulo de Métricas Semanales (RF11-RF14, RN03, HU2).

Verifica cumplimiento de:
- RF11: Cálculo de horas por día y promedio semanal con 1 decimal (solo días con registro).
- RF12 / RN03: Detección de días críticos comparando contra meta personal o 6.0h por defecto.
- Días sin registro: no son críticos y duracionHoras = null.
- RF13: Consulta de semanas anteriores enviando semana_inicio explícitamente.
- RF14: Respuesta clara si no hay datos suficientes (datosSuficientes: false).
- Aislamiento multi-usuario: un usuario solo ve y promedia sus propios registros.
"""

from datetime import date, time
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user_id,
    get_metrics_service,
    get_sleep_record_repository,
    get_sleep_record_service,
    get_user_profile_repository,
)
from app.main import app
from app.models.sleep_record import RegistroSueno
from app.models.user_profile import PerfilUsuario
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.metrics_service import MetricsService
from app.services.sleep_record_service import SleepRecordService

USER_CON_META = "00000000-0000-0000-0000-000000000001"
USER_SIN_META = "00000000-0000-0000-0000-000000000002"


@pytest.fixture
def sleep_repo():
    return SleepRecordRepository(client=None)


@pytest.fixture
def profile_repo():
    repo = UserProfileRepository(client=None, is_test_mode=True)
    # Usuario 1 con meta personal de 8.0 horas
    repo.create(
        PerfilUsuario(
            id=USER_CON_META,
            email="con.meta@universidad.edu",
            nombre="Usuario",
            apellido="Con Meta",
            ocupacion="Estudiante",
            meta_sueno=8.0,
        )
    )
    # Usuario 2 sin meta (meta_sueno = None)
    repo.create(
        PerfilUsuario(
            id=USER_SIN_META,
            email="sin.meta@universidad.edu",
            nombre="Usuario",
            apellido="Sin Meta",
            ocupacion="Trabajador",
            meta_sueno=None,
        )
    )
    return repo


@pytest.fixture
def metrics_service(sleep_repo, profile_repo):
    return MetricsService(sleep_repo=sleep_repo, profile_repo=profile_repo)


@pytest.fixture
def client_con_meta(sleep_repo, profile_repo, metrics_service):
    app.dependency_overrides[get_sleep_record_repository] = lambda: sleep_repo
    app.dependency_overrides[get_user_profile_repository] = lambda: profile_repo
    app.dependency_overrides[get_metrics_service] = lambda: metrics_service
    app.dependency_overrides[get_current_user_id] = lambda: USER_CON_META
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_sin_meta(sleep_repo, profile_repo, metrics_service):
    app.dependency_overrides[get_sleep_record_repository] = lambda: sleep_repo
    app.dependency_overrides[get_user_profile_repository] = lambda: profile_repo
    app.dependency_overrides[get_metrics_service] = lambda: metrics_service
    app.dependency_overrides[get_current_user_id] = lambda: USER_SIN_META
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_metricas_semana_sin_registros_retorna_datos_insuficientes_rf14(client_con_meta):
    """RF14: Si no hay registros en la semana, responde con datosSuficientes: false y mensaje informativo."""
    # Lunes 2026-10-05 a Domingo 2026-10-11
    response = client_con_meta.get("/api/v1/metrics/weekly?semana_inicio=2026-10-05")
    assert response.status_code == 200

    data = response.json()
    assert data["datosSuficientes"] is False
    assert data["promedioHoras"] is None
    assert "No se encontraron registros" in data["mensaje"]
    assert len(data["dias"]) == 7
    # Todos los días deben tener duracionHoras = None y esCritico = False
    for dia in data["dias"]:
        assert dia["duracionHoras"] is None
        assert dia["esCritico"] is False


def test_metricas_semanales_con_meta_definida_rn03_y_promedio_rf11(client_con_meta, sleep_repo):
    """RF11, RF12, RN03: Con meta de 8.0h, promedio calculado solo sobre días con registro y días < 8.0 son críticos."""
    # Insertar 3 días de descanso en la semana del lunes 2026-10-05:
    # Lunes 2026-10-05: 8.5h (No crítico, >= 8.0)
    # Martes 2026-10-06: 7.0h (Crítico, < 8.0)
    # Miércoles 2026-10-07: 6.5h (Crítico, < 8.0)
    # Jueves a Domingo: sin registro (duracionHoras=null, esCritico=false)
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_CON_META,
            fecha=date(2026, 10, 5),
            hora_acostarse=time(22, 0),
            hora_despertar=time(6, 30),
            calificacion=4,
            duracion_horas=8.5,
        )
    )
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_CON_META,
            fecha=date(2026, 10, 6),
            hora_acostarse=time(23, 0),
            hora_despertar=time(6, 0),
            calificacion=3,
            duracion_horas=7.0,
        )
    )
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_CON_META,
            fecha=date(2026, 10, 7),
            hora_acostarse=time(23, 30),
            hora_despertar=time(6, 0),
            calificacion=3,
            duracion_horas=6.5,
        )
    )

    response = client_con_meta.get("/api/v1/metrics/weekly?semana_inicio=2026-10-05")
    assert response.status_code == 200
    data = response.json()

    assert data["datosSuficientes"] is True
    assert data["metaSuenoAplicada"] == 8.0

    # Promedio de [8.5, 7.0, 6.5] = 22.0 / 3 = 7.3333 -> 7.3 con 1 decimal (RF11)
    assert data["promedioHoras"] == 7.3

    # Días críticos: Martes 2026-10-06 y Miércoles 2026-10-07 (RF12, RN03)
    assert len(data["diasCriticos"]) == 2
    assert "2026-10-06" in data["diasCriticos"]
    assert "2026-10-07" in data["diasCriticos"]

    # Verificar proyección de días
    dias = data["dias"]
    assert len(dias) == 7
    assert dias[0]["diaSemana"] == "Lunes"
    assert dias[0]["duracionHoras"] == 8.5
    assert dias[0]["esCritico"] is False

    assert dias[1]["diaSemana"] == "Martes"
    assert dias[1]["duracionHoras"] == 7.0
    assert dias[1]["esCritico"] is True

    assert dias[2]["diaSemana"] == "Miércoles"
    assert dias[2]["duracionHoras"] == 6.5
    assert dias[2]["esCritico"] is True

    # Días sin registro: no son críticos y duracionHoras = None
    assert dias[3]["diaSemana"] == "Jueves"
    assert dias[3]["duracionHoras"] is None
    assert dias[3]["esCritico"] is False


def test_metricas_semanales_sin_meta_usa_umbral_por_defecto_6h_rn03(client_sin_meta, sleep_repo):
    """RN03: Si el usuario no tiene meta personal, se aplica el umbral de 6.0 horas."""
    # Lunes 2026-10-05: 6.5h -> No es crítico (>= 6.0)
    # Martes 2026-10-06: 5.5h -> Es crítico (< 6.0)
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_SIN_META,
            fecha=date(2026, 10, 5),
            hora_acostarse=time(23, 30),
            hora_despertar=time(6, 0),
            calificacion=3,
            duracion_horas=6.5,
        )
    )
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_SIN_META,
            fecha=date(2026, 10, 6),
            hora_acostarse=time(0, 30),
            hora_despertar=time(6, 0),
            calificacion=2,
            duracion_horas=5.5,
        )
    )

    response = client_sin_meta.get("/api/v1/metrics/weekly?semana_inicio=2026-10-05")
    assert response.status_code == 200
    data = response.json()

    assert data["metaSuenoAplicada"] == 6.0
    # Promedio [6.5, 5.5] = 12.0 / 2 = 6.0
    assert data["promedioHoras"] == 6.0
    assert len(data["diasCriticos"]) == 1
    assert "2026-10-06" in data["diasCriticos"]


def test_navegacion_semanas_anteriores_rf13(client_con_meta, sleep_repo):
    """RF13: Consultar semanas anteriores pasando semana_inicio explícitamente."""
    # Semana pasada: Lunes 2026-09-28 a Domingo 2026-10-04
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_CON_META,
            fecha=date(2026, 9, 29),
            hora_acostarse=time(22, 0),
            hora_despertar=time(6, 0),
            calificacion=4,
            duracion_horas=8.0,
        )
    )

    # Consulta semana anterior
    res_ant = client_con_meta.get("/api/v1/metrics/weekly?semana_inicio=2026-09-28")
    assert res_ant.status_code == 200
    data_ant = res_ant.json()
    assert data_ant["semanaInicio"] == "2026-09-28"
    assert data_ant["semanaFin"] == "2026-10-04"
    assert data_ant["datosSuficientes"] is True
    assert data_ant["promedioHoras"] == 8.0

    # Consulta semana siguiente (2026-10-05 sin los registros anteriores): debe ser independiente
    res_sig = client_con_meta.get("/api/v1/metrics/weekly?semana_inicio=2026-10-05")
    assert res_sig.status_code == 200
    data_sig = res_sig.json()
    assert data_sig["datosSuficientes"] is False


def test_aislamiento_metricas_multi_usuario(client_sin_meta, sleep_repo):
    """Un usuario solo puede ver sus propios registros; no promedia registros ajenos."""
    # Insertar registro solo para USER_CON_META
    sleep_repo.create(
        RegistroSueno(
            id_registro=None,
            id_usuario=USER_CON_META,
            fecha=date(2026, 10, 5),
            hora_acostarse=time(22, 0),
            hora_despertar=time(6, 0),
            calificacion=4,
            duracion_horas=8.0,
        )
    )

    # USER_SIN_META consulta la misma semana y no debe ver registros ajenos
    res = client_sin_meta.get("/api/v1/metrics/weekly?semana_inicio=2026-10-05")
    assert res.status_code == 200
    assert res.json()["datosSuficientes"] is False
    assert res.json()["promedioHoras"] is None
