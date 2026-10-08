# Progreso del Proyecto SleepTrack

Documento de seguimiento del estado del sistema, componentes implementados, decisiones técnicas, pendientes y guías de ejecución.

---

## 1. Qué Quedó Implementado (con Rutas)

Se implementó el backend del **Módulo de Autenticación y Usuarios (RF01, RF02, RF10, RNF01, RNF02)**, el **Módulo de Registro de Sueño (HU1: RF03-RF09, RN01, RN02)** y el **Módulo de Métricas Semanales (HU2: RF11-RF14, RN03)** bajo el patrón en tres capas **Router → Service → Repository**.

### 1.1 Rutas y Endpoints HTTP
- `POST /api/v1/auth/register`: Registrar nuevo usuario con Supabase Auth y crear su perfil (RF01, RNF01, RNF02).
  - Almacena contraseñas cifradas en Supabase Auth (`auth.users`, RNF01).
  - Persiste los datos de perfil (nombre, apellido, ocupación, meta de sueño) en la tabla `perfiles_usuario` (RNF04).
  - Retorna HTTP `201 Created` con tokens de sesión JWT (`access_token`, `refresh_token`, `expires_in`, RNF02) y perfil del usuario.
  - Si el correo ya existe, retorna HTTP `409 Conflict`.
- `POST /api/v1/auth/login`: Autenticación con correo y contraseña (RF02, RNF02).
  - Valida credenciales contra Supabase Auth y emite token de sesión con expiración (RNF02).
  - Retorna HTTP `200 OK` o HTTP `401 Unauthorized` si las credenciales son incorrectas.
- `DELETE /api/v1/users/me?confirmar=true`: Eliminar cuenta propia y todos los datos asociados en cascada (**RF10**).
  - Requiere confirmación explícita mediante query parameter `confirmar=true`. Si no se pasa o es `false`, retorna `400 Bad Request`.
  - Emplea la API administrativa de Supabase Auth con `service_role` (`admin.delete_user`), desencadenando el borrado en cascada en PostgreSQL (`ON DELETE CASCADE`) para `perfiles_usuario` y `registros_sueno`.
  - Retorna HTTP `204 No Content`.
- `POST /api/v1/sleep-records`: Crear registro diario de sueño (requiere autenticación Bearer token, RNF02).
  - Valida unicidad de 1 registro por usuario y fecha (**RN01**). Si ya existe, retorna HTTP `409 Conflict` con el ID del registro existente orientando a editarlo (**RF08**).
  - Valida que la hora de acostarse no sea futura contra el reloj en tiempo real (**RN02**, **RF05**). Si es futura, retorna HTTP `400 Bad Request`.
  - Valida campos obligatorios y formato de hora (**RF06**), y calificación en escala 1 a 5 (**RF03**, **RF05**). Si falla, retorna HTTP `422 Unprocessable Entity` o `400 Bad Request`.
  - Calcula automáticamente la duración en horas cruzando medianoche (**RF04**).
  - Retorna confirmación inmediata (**RF08**) con HTTP `201 Created`.
- `GET /api/v1/sleep-records/by-date/{fecha}`: Consulta de existencia de registro para una fecha (permite al cliente móvil detectar duplicados y ofrecer edición previa, **RF08**, **RN01**). Retorna `200 OK` o `404 Not Found`. Requiere token Bearer (RNF02).
- `PUT /api/v1/sleep-records/{id_registro}`: Editar un registro existente para una fecha (**RF08**). Recalcula la duración (**RF04**) y valida hora no futura (**RN02**). Retorna `200 OK`. Requiere token Bearer (RNF02).
- `DELETE /api/v1/sleep-records/{id_registro}`: Eliminar un registro de sueño propio (**RF09**).
  - Retorna HTTP `204 No Content`.
  - Si el registro no existe o pertenece a otro usuario, responde HTTP `404 Not Found` (nunca `403`), evitando fuga de información entre cuentas.
- `GET /api/v1/metrics/weekly`: Resumen semanal dinámico y detección de días críticos (**RF11-RF14, RN03, HU2**).
  - Parámetro opcional: `semana_inicio=YYYY-MM-DD` (Lunes). Permite navegar a semanas anteriores (**RF13**).
  - Si se omite, calcula por defecto el Lunes de la semana actual basado en la fecha del servidor, recomendándose que el cliente envíe `semana_inicio` explícitamente.
  - La semana comprende 7 días (Lunes a Domingo). Turnos que cruzan medianoche se contabilizan en el día de la fecha de inicio del descanso.
  - Días con registro: calcula promedio semanal a 1 decimal (**RF11**).
  - Días sin registro: se retornan con `duracionHoras: null`, no son críticos y no afectan el promedio.
  - Días críticos (**RN03, RF12**): marcados cuando `duracion_horas < metaSueno` del perfil, o `< 6.0` horas por defecto si el usuario no tiene meta.
  - Si la semana no tiene ningún registro, retorna `datosSuficientes: false` con mensaje descriptivo (**RF14**).
  - Se calcula de forma dinámica directamente desde `registros_sueno` sin persistencia intermedia en tablas auxiliares.
- `GET /health`: Endpoint de monitoreo de disponibilidad del backend (**RNF03**).
- `GET /docs` y `GET /redoc`: Documentación interactiva automática OpenAPI Swagger.

### 1.2 Archivos del Código Fuente
- `app/main.py`: Punto de entrada FastAPI, configuración de prefijo `/api/v1`, registro de routers (`auth_router`, `users_router`, `sleep_records_router`, `metrics_router`), documentación OpenAPI y middleware de estandarización de errores 422.
- `app/api/routers/auth_router.py`: APIRouter para `/auth/register` y `/auth/login`.
- `app/api/routers/users_router.py`: APIRouter para `/users/me` (`DELETE` con `confirmar=true`, RF10).
- `app/api/routers/sleep_records_router.py`: APIRouter con endpoints HTTP de registros de sueño (`POST`, `GET /by-date`, `PUT`, `DELETE` RF09).
- `app/api/routers/metrics_router.py`: APIRouter con endpoint `GET /metrics/weekly` (RF11-RF14, RN03).
- `app/api/dependencies.py`: Inyección de dependencias para autenticación (`get_current_user_id`), repositorios (`get_user_profile_repository`, `get_sleep_record_repository`) y servicios (`get_auth_service`, `get_sleep_record_service`, `get_metrics_service`).
- `app/services/auth_service.py`: Lógica de autenticación, login y borrado de cuenta en cascada (`delete_user`, RF10) con modo seguro de tests.
- `app/services/sleep_record_service.py`: Lógica de negocio para registros de sueño (`create_sleep_record`, `update_sleep_record`, `delete_sleep_record` RF09, `get_records_by_date_range`).
- `app/services/metrics_service.py`: Servicio de cálculo dinámico semanal, proyección de 7 días, promedio con 1 decimal y detección de días críticos según RN03.
- `app/repositories/user_profile_repository.py`: Capa de persistencia para `perfiles_usuario` en Supabase con RLS y soporte de `meta_sueno` opcional.
- `app/repositories/sleep_record_repository.py`: Capa de persistencia para `registros_sueno` en Supabase con soporte de rango de fechas (`get_by_date_range`), borrado propio y clave foránea UUID.
- `app/models/user_profile.py`: Entidad de dominio `PerfilUsuario` (`meta_sueno: float | None`).
- `app/models/sleep_record.py`: Entidad de dominio `RegistroSueno` (`id_usuario: str`).
- `app/schemas/auth.py`: DTOs Pydantic v2 para Auth.
- `app/schemas/metrics.py`: DTOs Pydantic v2 para métricas (`WeeklyMetricsResponse`, `DiaMetricaResponse`).
- `app/schemas/sleep_record.py`: DTOs Pydantic v2 para registros de sueño con soporte `camelCase` y `snake_case`.
- `app/core/exceptions.py`: Jerarquía de excepciones de dominio.
- `app/core/config.py`: Configuraciones y detección de modo testing (`TESTING=true`).
- `supabase/schema_perfiles_usuario.sql`: Script DDL SQL para tabla `perfiles_usuario` vinculada a `auth.users(id)` con RLS.
- `supabase/migration_registros_sueno_uuid.sql`: Script de migración SQL para adaptar `registros_sueno.id_usuario` a UUID referenciando `auth.users(id)` con RLS.
- `tests/test_auth.py`: Suite de 9 pruebas de integración y unitarias para auth y eliminación de cuenta RF10.
- `tests/test_sleep_records.py`: Suite de 17 pruebas de dominio, endpoints protegidos, unicidad RN01 y eliminación propia RF09.
- `tests/test_metrics.py`: Suite de 5 pruebas exhaustivas para RF11-RF14, RN03 con meta, sin meta, semanas anteriores y aislamiento de usuarios.
- `tests/test_sleep_repository.py`: Suite de 5 pruebas unitarias de persistencia y conversión de tipos.

---

## 2. Decisiones Técnicas

1. **Gestión de Identidad y Eliminación en Cascada (RF10, RNF01, RNF02):**
   - La eliminación de cuenta en Supabase Auth se ejecuta con `client.auth.admin.delete_user(user_id)` mediante clave `service_role`.
   - Se requiere el parámetro de consulta obligatorio `confirmar=true`.
   - La base de datos PostgreSQL purga automáticamente en cascada `perfiles_usuario` y `registros_sueno` vía `ON DELETE CASCADE`.

2. **Cálculo Dinámico de Métricas (RF11-RF14, RN03):**
   - No se utiliza almacenamiento intermedio en `metrica_semanal`.
   - Las métricas se derivan directamente en tiempo de ejecución consultando `registros_sueno` en el rango `[semana_inicio, semana_inicio + 6]`.
   - La semana inicia formalmente el **Lunes** (ISO-8601) y finaliza el **Domingo**.
   - Los días sin descanso no penalizan el promedio ni se marcan como críticos; se retornan con `duracionHoras: null`.

3. **Seguridad y Fuga de Información en Eliminación (RF09):**
   - Cuando un usuario intenta eliminar un registro inexistente o que pertenece a otro usuario, el sistema responde siempre con **HTTP 404 Not Found** (nunca 403), imposibilitando la enumeración o detección de existencia de registros ajenos.

---

## 3. Qué Falta por Implementar

Basado estrictamente en los requisitos del informe técnico (`docs/informe3.md`):

### 3.1 Backend (FastAPI + Supabase)
- **Módulo de Usuarios (Endpoints restantes de HU1):**
  - Endpoints: `GET /api/v1/users/me`, `PUT /api/v1/users/me`.
- **Módulo de Registros de Sueño (Restante):**
  - Listado de registros históricos del usuario (`GET /api/v1/sleep-records`).
- **Módulo de Alertas de Higiene del Sueño (`RF15`–`RF18`, `RN04`, HU3):**
  - Endpoints `POST /api/v1/alerts`, `GET /api/v1/alerts`, `PUT /api/v1/alerts/{id_alerta}`, `PATCH /api/v1/alerts/{id_alerta}/toggle`, `DELETE /api/v1/alerts/{id_alerta}`.
  - Validación de no duplicidad de alertas por hora y tipo `DORMIR`/`DESPERTAR` para el usuario (**RN04**, **RF16**).
  - Desactivación sin eliminar el registro histórico (**RF18**).
- **Módulo de Consola Administrativa (`RF19`, HU4):**
  - Autenticación administrativa con auditoría de intentos fallidos (`POST /api/v1/admin/login`).
  - Reportes de actividad por rango de fechas (`GET /api/v1/admin/activity-report`).
  - Depuración manual de registros con registro de auditoría (`DELETE /api/v1/admin/sleep-records/{id_registro}`).
  - Exportación de respaldos cifrados del sistema (`GET /api/v1/admin/backup/export`).
- **Base de Datos Supabase:**
  - Pendiente migración DDL para los módulos restantes (`alertas`, `auditoria`).

### 3.2 Cliente Móvil / Web
- Implementación de pantallas e interfaces para Estudiantes/Trabajadores (HU1 a HU3) y Administradores (HU4).

---

## 4. Cómo Correr el Servidor y Pytest

### 4.1 Requisitos Previos
- Python 3.11+ instalado.
- Entorno virtual configurado en la raíz del proyecto.

### 4.2 Activación del Entorno Virtual e Instalación de Dependencias

En Windows (PowerShell):
```powershell
# Crear entorno virtual (si no existe)
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.3 Ejecutar las Pruebas con Pytest

Para ejecutar la suite completa de pruebas:
```powershell
pytest -v
```

Para ejecutar una prueba específica:
```powershell
pytest tests/test_sleep_records.py -k "test_calcular_duracion_cruzando_medianoche" -v
```

### 4.4 Iniciar el Servidor de Desarrollo con Uvicorn

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Una vez iniciado el servidor:
- **API Base:** `http://127.0.0.1:8000/api/v1/sleep-records`
- **Documentación Swagger UI:** `http://127.0.0.1:8000/docs`
- **Documentación ReDoc:** `http://127.0.0.1:8000/redoc`
- **Verificación de Salud:** `http://127.0.0.1:8000/health`
