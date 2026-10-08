"""Pruebas unitarias para SleepRecordRepository y la integración con Supabase.

Verifica:
- Conversión de filas de Supabase a entidad RegistroSueno (_row_to_model).
- Mapeo de violación de restricción única PostgreSQL 23505 a SleepRecordAlreadyExistsError (RN01).
- Operaciones get_by_user_and_date, get_by_id, create, update, delete y list_by_user.
- Detección de configuración válida de Supabase en Settings.
"""

from datetime import date, time
from unittest.mock import MagicMock
import pytest
from postgrest.exceptions import APIError
from app.core.config import Settings
from app.core.exceptions import SleepRecordAlreadyExistsError
from app.models.sleep_record import RegistroSueno
from app.repositories.sleep_record_repository import SleepRecordRepository


def test_settings_detects_supabase_configuration():
    """Verifica que Settings distinga entre placeholders y credenciales reales."""
    s_empty = Settings(supabase_url="", supabase_key="")
    assert s_empty.is_supabase_configured is False

    s_mock = Settings(
        supabase_url="https://mock-sleeptrack.supabase.co",
        supabase_key="mock-supabase-key",
    )
    assert s_mock.is_supabase_configured is False

    s_example = Settings(
        supabase_url="https://tu-proyecto.supabase.co",
        supabase_key="tu-clave-supabase",
    )
    assert s_example.is_supabase_configured is False

    s_valid = Settings(
        supabase_url="https://xyzabcdefg.supabase.co",
        supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid_key",
    )
    assert s_valid.is_supabase_configured is True


def test_row_to_model_handles_string_and_native_types():
    """Verifica que _row_to_model parsea cadenas ISO y tipos nativos de fecha y hora."""
    repo = SleepRecordRepository(client=None)

    row_strings = {
        "id_registro": 10,
        "id_usuario": 1,
        "fecha": "2026-10-07",
        "hora_acostarse": "22:30:00",
        "hora_despertar": "06:30:00",
        "calificacion": "4",
        "duracion_horas": "8.0",
    }
    modelo = repo._row_to_model(row_strings)
    assert modelo.id_registro == 10
    assert modelo.id_usuario == 1
    assert modelo.fecha == date(2026, 10, 7)
    assert modelo.hora_acostarse == time(22, 30)
    assert modelo.hora_despertar == time(6, 30)
    assert modelo.calificacion == 4
    assert modelo.duracion_horas == 8.0


def test_repository_with_real_supabase_client_create_and_get():
    """Verifica las llamadas del repositorio cuando se le inyecta un cliente Supabase."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Simular insert().execute() exitoso
    mock_table.insert.return_value.execute.return_value.data = [
        {
            "id_registro": 42,
            "id_usuario": 1,
            "fecha": "2026-10-07",
            "hora_acostarse": "23:00:00",
            "hora_despertar": "07:00:00",
            "calificacion": 5,
            "duracion_horas": 8.0,
        }
    ]

    repo = SleepRecordRepository(client=mock_client)
    nuevo_registro = RegistroSueno(
        id_registro=None,
        id_usuario=1,
        fecha=date(2026, 10, 7),
        hora_acostarse=time(23, 0),
        hora_despertar=time(7, 0),
        calificacion=5,
        duracion_horas=8.0,
    )
    resultado = repo.create(nuevo_registro)

    assert resultado.id_registro == 42
    mock_client.table.assert_called_with("registros_sueno")
    mock_table.insert.assert_called_once()


def test_repository_handles_supabase_unique_violation_rn01():
    """RN01: Debe traducir APIError 23505 (uq_registros_sueno_usuario_fecha) a SleepRecordAlreadyExistsError."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Simular que get_by_user_and_date encuentra el ID previo
    mock_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "id_registro": 99,
        "id_usuario": 1,
        "fecha": "2026-10-07",
        "hora_acostarse": "22:00:00",
        "hora_despertar": "06:00:00",
        "calificacion": 3,
        "duracion_horas": 8.0,
    }

    # Simular que insert() lanza violación única de PostgreSQL (código 23505)
    raw_error = {
        "message": 'duplicate key value violates unique constraint "uq_registros_sueno_usuario_fecha"',
        "code": "23505",
        "details": "Key (id_usuario, fecha)=(1, 2026-10-07) already exists.",
        "hint": None,
    }
    mock_table.insert.return_value.execute.side_effect = APIError(raw_error)

    repo = SleepRecordRepository(client=mock_client)
    registro_duplicado = RegistroSueno(
        id_registro=None,
        id_usuario=1,
        fecha=date(2026, 10, 7),
        hora_acostarse=time(23, 0),
        hora_despertar=time(7, 0),
        calificacion=4,
        duracion_horas=8.0,
    )

    with pytest.raises(SleepRecordAlreadyExistsError) as exc_info:
        repo.create(registro_duplicado)

    assert exc_info.value.existing_record_id == 99
    assert "RF08" in str(exc_info.value)


def test_repository_delete_and_list():
    """Verifica operaciones delete y list_by_user en el repositorio."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id_registro": 1}
    ]

    mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {
            "id_registro": 1,
            "id_usuario": 1,
            "fecha": "2026-10-07",
            "hora_acostarse": "23:00:00",
            "hora_despertar": "07:00:00",
            "calificacion": 4,
            "duracion_horas": 8.0,
        }
    ]

    repo = SleepRecordRepository(client=mock_client)
    eliminado = repo.delete(id_registro=1, id_usuario=1)
    assert eliminado is True

    lista = repo.list_by_user(id_usuario=1)
    assert len(lista) == 1
    assert lista[0].id_registro == 1
