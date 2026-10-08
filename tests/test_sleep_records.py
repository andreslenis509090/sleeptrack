"""Pruebas unitarias y de integración para el módulo de registro de sueño (HU1).

Verifica cumplimiento de:
- RF03: Registro manual de sueño (fecha, hora inicio, hora fin, calificación 1-5).
- RF04: Cálculo automático de duración de horas cruzando medianoche.
- RF05 / RN02: Validación de hora de inicio de sueño contra reloj en tiempo real.
- RF06: Validación de campos obligatorios y formatos válidos.
- RF08 / RN01: Unicidad de registro por fecha y redirección a edición.
"""

from datetime import date, datetime, time, timedelta
import pytest
from fastapi.testclient import TestClient
from app.api.dependencies import get_current_user_id, get_sleep_record_service
from app.core.exceptions import FutureSleepTimeError
from app.main import app
from app.models.sleep_record import RegistroSueno
from app.repositories.sleep_record_repository import SleepRecordRepository
from app.services.sleep_record_service import SleepRecordService

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def repo():
    """Provee un repositorio limpio en memoria para pruebas."""
    return SleepRecordRepository(client=None)


@pytest.fixture
def service(repo):
    """Provee el servicio de registros de sueño."""
    return SleepRecordService(repository=repo)


@pytest.fixture
def client(repo, service):
    """Provee un TestClient de FastAPI con repositorio, servicio y usuario autenticado simulado."""
    app.dependency_overrides[get_sleep_record_service] = lambda: service
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield TestClient(app)
    app.dependency_overrides.clear()


# ==============================================================================
# Pruebas Unitarias del Modelo de Dominio (RegistroSueno)
# ==============================================================================


def test_calcular_duracion_mismo_dia():
    """RF04: Cálculo de duración cuando inicio y fin ocurren el mismo día."""
    hora_inicio = time(14, 0)
    hora_fin = time(16, 30)
    duracion = RegistroSueno.calcular_duracion(hora_inicio, hora_fin)
    assert duracion == 2.5


def test_calcular_duracion_cruzando_medianoche():
    """RF04: Cálculo de duración cuando el descanso cruza la medianoche."""
    # De 23:00 a 07:00 del día siguiente son 8 horas
    hora_inicio = time(23, 0)
    hora_fin = time(7, 0)
    duracion = RegistroSueno.calcular_duracion(hora_inicio, hora_fin)
    assert duracion == 8.0

    # De 22:30 a 06:45 son 8.25 horas
    duracion_frac = RegistroSueno.calcular_duracion(time(22, 30), time(6, 45))
    assert duracion_frac == 8.25


def test_calcular_duracion_misma_hora_acostarse_y_despertar():
    """RF04: Cálculo cuando horaAcostarse y horaDespertar son idénticas (cruza ciclo completo de 24 horas)."""
    hora = time(22, 0)
    duracion = RegistroSueno.calcular_duracion(hora, hora)
    assert duracion == 24.0

    hora_mañana = time(8, 30)
    duracion_mañana = RegistroSueno.calcular_duracion(hora_mañana, hora_mañana)
    assert duracion_mañana == 24.0



def test_validar_hora_futura_rechaza_tiempo_futuro():
    """RF05, RN02: Debe lanzar FutureSleepTimeError si la hora es posterior a la actual."""
    ahora = datetime(2026, 10, 7, 22, 0, 0)

    # Misma fecha pero hora futura (23:00 vs 22:00)
    with pytest.raises(FutureSleepTimeError):
        RegistroSueno.validar_hora_futura(
            fecha=date(2026, 10, 7),
            hora_acostarse=time(23, 0),
            now=ahora,
        )

    # Fecha posterior
    with pytest.raises(FutureSleepTimeError):
        RegistroSueno.validar_hora_futura(
            fecha=date(2026, 10, 8),
            hora_acostarse=time(21, 0),
            now=ahora,
        )


def test_validar_hora_futura_acepta_tiempo_pasado_o_presente():
    """RF05, RN02: Debe permitir horas en el pasado o exactas."""
    ahora = datetime(2026, 10, 7, 22, 0, 0)

    # Hora pasada en la misma fecha
    valido = RegistroSueno.validar_hora_futura(
        fecha=date(2026, 10, 7),
        hora_acostarse=time(21, 30),
        now=ahora,
    )
    assert valido is True


def test_validar_hora_futura_limite_exacto_ahora_mismo():
    """RN02, RF05: En el límite exacto de ahora mismo (inicio_dt == now), es aceptado (no es futuro)."""
    ahora = datetime(2026, 10, 7, 14, 30, 0)

    # 1. Exactamente en el instante actual: No debe lanzar excepción
    valido_exacto = RegistroSueno.validar_hora_futura(
        fecha=ahora.date(),
        hora_acostarse=ahora.time(),
        now=ahora,
    )
    assert valido_exacto is True

    # 2. Apenas un segundo en el futuro (14:30:01 vs 14:30:00): Debe lanzar FutureSleepTimeError
    un_segundo_despues = (ahora + timedelta(seconds=1)).time()
    with pytest.raises(FutureSleepTimeError):
        RegistroSueno.validar_hora_futura(
            fecha=ahora.date(),
            hora_acostarse=un_segundo_despues,
            now=ahora,
        )



# ==============================================================================
# Pruebas de Integración con FastAPI TestClient (Router -> Service -> Repository)
# ==============================================================================


def test_crear_registro_sueno_exitoso(client):
    """RF03, RF04, RF08: Creación exitosa calculando duración cruzando medianoche."""
    payload = {
        "fecha": "2026-10-06",
        "horaAcostarse": "23:00",
        "horaDespertar": "07:30",
        "calificacion": 4,
    }
    response = client.post("/api/v1/sleep-records", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["fecha"] == "2026-10-06"
    assert data["horaAcostarse"] == "23:00:00"
    assert data["horaDespertar"] == "07:30:00"
    assert data["calificacion"] == 4
    assert data["duracionHoras"] == 8.5
    assert "exitosamente" in data["mensaje"]


def test_crear_registro_sueno_rechaza_hora_futura_rn02(client):
    """RN02, RF05: Debe rechazar con HTTP 400 cuando la hora de acostarse está en el futuro."""
    manana = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "fecha": manana,
        "horaAcostarse": "22:00",
        "horaDespertar": "06:00",
        "calificacion": 3,
    }
    response = client.post("/api/v1/sleep-records", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "FUTURE_TIME_NOT_ALLOWED"


def test_crear_registro_duplicado_mismo_dia_rechaza_rn01_y_ofrece_rf08(client):
    """RN01, RF08: Unicidad de 1 registro por fecha. Segundo intento retorna HTTP 409."""
    payload = {
        "fecha": "2026-10-05",
        "horaAcostarse": "22:00",
        "horaDespertar": "06:00",
        "calificacion": 3,
    }
    # Primer registro: Exitoso (201)
    res1 = client.post("/api/v1/sleep-records", json=payload)
    assert res1.status_code == 201
    primer_id = res1.json()["idRegistro"]

    # Segundo registro para la misma fecha: Bloqueado (409)
    res2 = client.post("/api/v1/sleep-records", json=payload)
    assert res2.status_code == 409
    data_error = res2.json()

    assert data_error["detail"]["code"] == "RECORD_ALREADY_EXISTS"
    assert data_error["detail"]["existing_record_id"] == primer_id
    assert "RF08" in data_error["detail"]["message"]


def test_validacion_campos_y_calificacion_rf06(client):
    """RF06: Rechazar valores de calificación fuera de [1, 5] o tipos inválidos."""
    # Calificación 6 (fuera de rango)
    payload_invalido = {
        "fecha": "2026-10-04",
        "horaAcostarse": "22:00",
        "horaDespertar": "06:00",
        "calificacion": 6,
    }
    response = client.post("/api/v1/sleep-records", json=payload_invalido)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "calificacion" in str(data["error"]["field"])

    # Calificación 0
    payload_invalido["calificacion"] = 0
    response2 = client.post("/api/v1/sleep-records", json=payload_invalido)
    assert response2.status_code == 422


def test_consultar_registro_por_fecha_rf08(client):
    """RF08, RN01: Consultar existencia de un registro por fecha."""
    # Fecha sin registro -> 404
    res_404 = client.get("/api/v1/sleep-records/by-date/2026-09-30")
    assert res_404.status_code == 404

    # Crear registro
    client.post(
        "/api/v1/sleep-records",
        json={
            "fecha": "2026-09-30",
            "horaAcostarse": "21:30",
            "horaDespertar": "06:00",
            "calificacion": 5,
        },
    )

    # Ahora debe retornar 200 con los datos
    res_200 = client.get("/api/v1/sleep-records/by-date/2026-09-30")
    assert res_200.status_code == 200
    assert res_200.json()["calificacion"] == 5
    assert res_200.json()["duracionHoras"] == 8.5


def test_editar_registro_existente_rf08(client):
    """RF08: Edición de un registro existente con recálculo de duración (RF04)."""
    # 1. Crear registro inicial (22:00 a 06:00 = 8h, calif: 3)
    res_crear = client.post(
        "/api/v1/sleep-records",
        json={
            "fecha": "2026-10-01",
            "horaAcostarse": "22:00",
            "horaDespertar": "06:00",
            "calificacion": 3,
        },
    )
    assert res_crear.status_code == 201
    id_registro = res_crear.json()["idRegistro"]

    # 2. Editar registro (nueva hora: 23:00 a 08:00 = 9h, calif: 5)
    payload_edit = {
        "horaAcostarse": "23:00",
        "horaDespertar": "08:00",
        "calificacion": 5,
    }
    res_edit = client.put(f"/api/v1/sleep-records/{id_registro}", json=payload_edit)
    assert res_edit.status_code == 200
    data_edit = res_edit.json()

    assert data_edit["idRegistro"] == id_registro
    assert data_edit["duracionHoras"] == 9.0
    assert data_edit["calificacion"] == 5
    assert "actualizado exitosamente" in data_edit["mensaje"]


def test_crear_registro_sueno_misma_hora_acostarse_y_despertar_rf04(client):
    """RF04: Creación de registro vía API con horaAcostarse y horaDespertar idénticas (24.0 horas)."""
    payload = {
        "fecha": "2026-09-25",
        "horaAcostarse": "08:00",
        "horaDespertar": "08:00",
        "calificacion": 4,
    }
    response = client.post("/api/v1/sleep-records", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["duracionHoras"] == 24.0


def test_crear_registro_sueno_limite_ahora_mismo_rn02(client):
    """RN02, RF05: Registro vía API en la fecha de hoy con la hora actual exacta."""
    ahora = datetime.now()
    payload = {
        "fecha": ahora.date().isoformat(),
        "horaAcostarse": ahora.time().strftime("%H:%M:%S"),
        "horaDespertar": ahora.time().strftime("%H:%M:%S"),
        "calificacion": 4,
    }
    response = client.post("/api/v1/sleep-records", json=payload)
    # Debe ser aceptado (no es futuro) y retornar 201
    assert response.status_code == 201


def test_rn01_permite_misma_fecha_para_usuarios_distintos(service):
    """RN01: La restricción de unicidad es por usuario: dos usuarios pueden registrar la misma fecha."""
    user_1 = "00000000-0000-0000-0000-000000000001"
    user_2 = "00000000-0000-0000-0000-000000000002"
    fecha = date(2026, 10, 5)

    payload_1 = {
        "fecha": fecha.isoformat(),
        "horaAcostarse": "22:00",
        "horaDespertar": "06:00",
        "calificacion": 4,
    }
    from app.schemas.sleep_record import SleepRecordCreate
    reg1 = service.create_sleep_record(id_usuario=user_1, data=SleepRecordCreate(**payload_1))
    assert reg1.id_usuario == user_1

    # Usuario 2 registra la misma fecha: debe permitirse exitosamente
    reg2 = service.create_sleep_record(id_usuario=user_2, data=SleepRecordCreate(**payload_1))
    assert reg2.id_usuario == user_2
    assert reg2.fecha == fecha


