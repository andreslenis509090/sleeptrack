---
name: api-backend
description: Usar esta skill para diseñar, implementar, probar y mantener la API REST con FastAPI (Python), definiendo routers, servicios, repositorios con Supabase, esquemas Pydantic v2, validaciones de reglas de negocio y manejo estandarizado de errores HTTP.
---

# Skill: API Backend (FastAPI + Supabase)

Esta skill define la especificación técnica de la API REST construida con **FastAPI**, siguiendo la arquitectura en capas **Router → Service → Repository**, con base de datos en la nube en **Supabase** (PostgreSQL) y sin almacenamiento local.

---

## 1. Arquitectura en Capas

```
app/
├── api/
│   ├── dependencies.py          # Inyección de dependencias (Auth, DB, Services)
│   └── routers/
│       ├── auth_router.py       # RF01, RF02, RNF01, RNF02
│       ├── users_router.py      # RF01, RF10
│       ├── sleep_records_router.py # RF03-RF09, RN01, RN02 (HU1)
│       ├── metrics_router.py    # RF11-RF14, RN03 (HU2)
│       ├── alerts_router.py     # RF15-RF18, RN04 (HU3)
│       └── admin_router.py      # RF19 (HU4)
├── core/
│   ├── config.py                # Variables de entorno y conexión Supabase
│   ├── security.py              # Hash de contraseñas y JWT con expiración (RNF01, RNF02)
│   └── exceptions.py            # Jerarquía de excepciones de dominio
├── models/                      # Entidades del dominio
├── schemas/                     # DTOs y validaciones Pydantic v2
├── services/                    # Capa de Lógica de Negocio y Reglas (RN01 - RN04)
│   ├── auth_service.py
│   ├── user_service.py
│   ├── sleep_record_service.py
│   ├── metrics_service.py
│   ├── alert_service.py
│   └── admin_service.py
└── repositories/                # Capa de Persistencia con Supabase Client
    ├── user_repository.py
    ├── sleep_record_repository.py
    ├── alert_repository.py
    └── admin_repository.py
```

---

## 2. Definición de Endpoints por Módulo

### 2.1 Módulo de Autenticación y Usuarios (`RF01`, `RF02`, `RF10`, `RNF01`, `RNF02`)

| Método | Endpoint | Descripción | Requisito | Código Éxito | Códigos Error |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/register` | Registro de usuario (nombre, apellido, ocupación, metaSueño opcional, email, contraseña). Contraseña se almacena con hash seguro. | RF01, RNF01 | `201 Created` | `400`, `409 Conflict`, `422` |
| `POST` | `/api/v1/auth/login` | Autenticación con email y contraseña. Retorna token de sesión con expiración. | RF02, RNF02 | `200 OK` | `401 Unauthorized`, `422` |
| `GET` | `/api/v1/users/me` | Obtener perfil del usuario autenticado. | RF01 | `200 OK` | `401 Unauthorized` |
| `PUT` | `/api/v1/users/me` | Actualizar perfil (nombre, apellido, ocupación, metaSueño). | RF01 | `200 OK` | `400`, `401`, `422` |
| `DELETE` | `/api/v1/users/me` | Eliminar cuenta y todos los datos asociados en cascada. | RF10 | `204 No Content` | `401 Unauthorized` |

---

### 2.2 Módulo de Registro de Sueño (`RF03`–`RF09`, `RN01`, `RN02`, `HU1`)

| Método | Endpoint | Descripción | Requisito | Código Éxito | Códigos Error |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/sleep-records` | Crear registro diario de sueño (fecha, horaAcostarse, horaDespertar, calificación 1-5). Calcula duración (RF04), valida hora no futura (RN02) y verifica que no exista registro previo en la fecha (RN01). | RF03, RF04, RF05, RF06, RN01, RN02 | `201 Created` | `400`, `409 Conflict`, `422` |
| `GET` | `/api/v1/sleep-records` | Listar registros de sueño del usuario autenticado. | RF03 | `200 OK` | `401 Unauthorized` |
| `GET` | `/api/v1/sleep-records/by-date/{fecha}` | Consultar si existe un registro para una fecha específica (utilizado por el cliente para ofrecer edición RF08 antes de guardar). | RF08, RN01 | `200 OK` | `401`, `404 Not Found` |
| `PUT` | `/api/v1/sleep-records/{id_registro}` | Editar un registro de sueño existente para una fecha determinada (RF08). Recalcula duración (RF04) y valida RN02. | RF08, RF04, RN02 | `200 OK` | `400`, `401`, `404`, `422` |
| `DELETE` | `/api/v1/sleep-records/{id_registro}` | Eliminar un registro de sueño propio. | RF09 | `204 No Content` | `401`, `404 Not Found` |

---

### 2.3 Módulo de Métricas Semanales (`RF11`–`RF14`, `RN03`, `HU2`)

| Método | Endpoint | Descripción | Requisito | Código Éxito | Códigos Error |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/metrics/weekly` | Obtiene el resumen semanal de 7 días (horas dormidas por día, promedio semanal formateado a 1 decimal, identificación de días críticos según RN03). Parámetro opcional: `start_date` para navegación entre semanas anteriores (RF13). Si no hay registros, retorna estructura con flag `datos_suficientes: false` (RF14). | RF11, RF12, RF13, RF14, RN03 | `200 OK` | `400`, `401 Unauthorized` |

---

### 2.4 Módulo de Alertas de Higiene del Sueño (`RF15`–`RF18`, `RN04`, `HU3`)

| Método | Endpoint | Descripción | Requisito | Código Éxito | Códigos Error |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/alerts` | Configurar nueva alerta (hora, tipo: `DORMIR` o `DESPERTAR`). Valida que no exista duplicada (misma hora y tipo para el usuario, RN04). | RF15, RF16, RN04 | `201 Created` | `400`, `409 Conflict`, `422` |
| `GET` | `/api/v1/alerts` | Listar todas las alertas del usuario autenticado (activas e inactivas). | RF15, RF18 | `200 OK` | `401 Unauthorized` |
| `PUT` | `/api/v1/alerts/{id_alerta}` | Modificar la hora o tipo de una alerta existente. Valida RN04 contra otras alertas. | RF17, RN04 | `200 OK` | `400`, `401`, `404`, `409` |
| `PATCH` | `/api/v1/alerts/{id_alerta}/toggle` | Activar o desactivar una alerta sin eliminar su registro histórico en base de datos. | RF18 | `200 OK` | `401`, `404 Not Found` |
| `DELETE` | `/api/v1/alerts/{id_alerta}` | Eliminar una alerta programada. | RF15 | `204 No Content` | `401`, `404 Not Found` |

---

### 2.5 Módulo de Consola Administrativa (`RF19`, `HU4`)

| Método | Endpoint | Descripción | Requisito | Código Éxito | Códigos Error |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/admin/login` | Autenticación del administrador con credenciales válidas. Si falla, deniega acceso y registra intento fallido en log. | RF19, HU4, RNF06 | `200 OK` | `401 Unauthorized` |
| `GET` | `/api/v1/admin/activity-report` | Genera reporte de actividad por rango de fechas (`fecha_inicio`, `fecha_fin`). Retorna resumen estadístico de uso sin degradar rendimiento (RNF08). | RF19, HU4, RNF08 | `200 OK` | `400`, `401`, `403 Forbidden` |
| `DELETE` | `/api/v1/admin/sleep-records/{id_registro}` | Depuración manual de un registro erróneo por parte del administrador. Requiere confirmación y audita la acción. | RF19, HU4 | `204 No Content` | `401`, `403`, `404` |
| `GET` | `/api/v1/admin/backup/export` | Genera y descarga un archivo cifrado con el respaldo de seguridad de los datos del sistema. Registra acción en auditoría. | RF19, HU4 | `200 OK` | `401`, `403 Forbidden` |

---

## 3. Implementación de Validaciones y Reglas de Negocio en la Capa Service

### 3.1 Unicidad por Fecha (`RN01` / `RF08`)
- Antes de insertar en `POST /sleep-records`, el servicio consulta si existe un registro para `(id_usuario, fecha)`.
- Si ya existe, el servicio lanza `SleepRecordAlreadyExistsError` que el Router traduce a:
  ```json
  {
    "detail": "Ya existe un registro de sueño para esta fecha. Utilice la opción de edición (RF08).",
    "code": "RECORD_ALREADY_EXISTS",
    "existing_record_id": 123
  }
  ```
  HTTP Status: `409 Conflict`.

### 3.2 Hora de Inicio No Futura (`RN02` / `RF05`)
- Al crear o editar un registro, el servicio combina `fecha` y `horaAcostarse` y compara contra `datetime.now(timezone)`.
- Si el momento es posterior a la hora actual, se lanza `FutureSleepTimeError`:
  ```json
  {
    "detail": "No se puede registrar una hora de inicio de sueño en el futuro.",
    "code": "FUTURE_TIME_NOT_ALLOWED"
  }
  ```
  HTTP Status: `400 Bad Request`.

### 3.3 Cálculo Automático de Duración Cruzando Medianoche (`RF04`)
- La función de cálculo debe soportar turnos que cruzan la medianoche:
  ```python
  def calculate_sleep_duration(hora_acostarse: time, hora_despertar: time) -> float:
      inicio = datetime.combine(date.min, hora_acostarse)
      fin = datetime.combine(date.min, hora_despertar)
      if fin <= inicio:
          # El sueño cruzó la medianoche
          fin += timedelta(days=1)
      duracion_segundos = (fin - inicio).total_seconds()
      return round(duracion_segundos / 3600.0, 2)
  ```

### 3.4 Identificación de Días Críticos (`RN03` / `RF12`)
- Umbral de meta: Si `usuario.meta_sueno` está definido, se usa ese valor; si es `None` o no definido, se aplica el umbral por defecto de **6.0 horas**.
- Un día registrado es crítico si: `duracion_horas < meta_aplicable`.
- En el endpoint de métricas, cada día incluye el flag: `es_critico: bool`.

### 3.5 Alertas Duplicadas (`RN04` / `RF16`)
- Antes de registrar o modificar una alerta, verificar si ya existe una alerta activa o inactiva para el mismo usuario con la misma hora y el mismo tipo (`DORMIR` o `DESPERTAR`).
- Si existe duplicado, lanzar `DuplicateAlertError` -> HTTP `409 Conflict`:
  ```json
  {
    "detail": "Ya existe una alerta con la misma hora y tipo para este usuario.",
    "code": "DUPLICATE_ALERT"
  }
  ```

### 3.6 Validación de Campos Obligatorios y Formatos (`RF06`)
- FastAPI y Pydantic validan tipos, formatos de hora (`HH:MM` o ISO) y campos obligatorios.
- Los errores 422 deben retornar mensajes claros e individualizados para cada campo fallido.

---

## 4. Respuestas de Error Estandarizadas

Todos los errores de la API deben seguir la estructura estándar:

```json
{
  "error": {
    "code": "NOMBRE_ERROR",
    "message": "Descripción legible para el usuario o cliente móvil",
    "field": "horaAcostarse"
  }
}
```

### Tabla de Códigos HTTP del Backend:
- `200 OK`: Consulta o actualización exitosa.
- `201 Created`: Creación exitosa de usuario, registro de sueño o alerta.
- `204 No Content`: Eliminación exitosa sin cuerpo de retorno.
- `400 Bad Request`: Formato de hora inválido, campos vacíos o intento de fecha/hora futura (RF06, RN02).
- `401 Unauthorized`: Token faltante, expirado (RNF02) o credenciales incorrectas.
- `403 Forbidden`: Operación administrativa intentada por usuario sin permisos.
- `404 Not Found`: Recurso no encontrado (registro de sueño o alerta inexistente).
- `409 Conflict`: Violación de unicidad de registro de sueño (RN01) o alerta duplicada (RN04).
- `422 Unprocessable Entity`: Fallo de validación de esquema en payload Pydantic.
- `500 Internal Server Error`: Excepción no controlada; se registra en log con trazabilidad (RNF06).
