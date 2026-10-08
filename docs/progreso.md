# Progreso del Proyecto SleepTrack

Documento de seguimiento del estado del sistema, componentes implementados, decisiones técnicas, pendientes y guías de ejecución.

---

## 1. Qué Quedó Implementado (con Rutas)

Se implementó el backend del **Módulo de Autenticación y Perfiles de Usuario (RF01, RF02, RNF01, RNF02)** y el **Módulo de Registro de Sueño (HU1: RF03-RF08, RN01, RN02)** bajo el patrón en tres capas **Router → Service → Repository**.

### 1.1 Rutas y Endpoints HTTP
- `POST /api/v1/auth/register`: Registrar nuevo usuario con Supabase Auth y crear su perfil (RF01, RNF01, RNF02).
  - Almacena contraseñas cifradas en Supabase Auth (`auth.users`, RNF01).
  - Persiste los datos de perfil (nombre, apellido, ocupación, meta de sueño) en la tabla `perfiles_usuario` (RNF04).
  - Retorna HTTP `201 Created` con tokens de sesión JWT (`access_token`, `refresh_token`, `expires_in`, RNF02) y perfil del usuario.
  - Si el correo ya existe, retorna HTTP `409 Conflict`.
- `POST /api/v1/auth/login`: Autenticación con correo y contraseña (RF02, RNF02).
  - Valida credenciales contra Supabase Auth y emite token de sesión con expiración (RNF02).
  - Retorna HTTP `200 OK` o HTTP `401 Unauthorized` si las credenciales son incorrectas.
- `POST /api/v1/sleep-records`: Crear registro diario de sueño (requiere autenticación Bearer token, RNF02).
  - Valida unicidad de 1 registro por usuario y fecha (**RN01**). Si ya existe, retorna HTTP `409 Conflict` con el ID del registro existente orientando a editarlo (**RF08**).
  - Valida que la hora de acostarse no sea futura contra el reloj en tiempo real (**RN02**, **RF05**). Si es futura, retorna HTTP `400 Bad Request`.
  - Valida campos obligatorios y formato de hora (**RF06**), y calificación en escala 1 a 5 (**RF03**, **RF05**). Si falla, retorna HTTP `422 Unprocessable Entity` o `400 Bad Request`.
  - Calcula automáticamente la duración en horas cruzando medianoche (**RF04**).
  - Retorna confirmación inmediata (**RF08**) con HTTP `201 Created`.
- `GET /api/v1/sleep-records/by-date/{fecha}`: Consulta de existencia de registro para una fecha (permite al cliente móvil detectar duplicados y ofrecer edición previa, **RF08**, **RN01**). Retorna `200 OK` o `404 Not Found`. Requiere token Bearer (RNF02).
- `PUT /api/v1/sleep-records/{id_registro}`: Editar un registro existente para una fecha (**RF08**). Recalcula la duración (**RF04**) y valida hora no futura (**RN02**). Retorna `200 OK`. Requiere token Bearer (RNF02).
- `GET /health`: Endpoint de monitoreo de disponibilidad del backend (**RNF03**).
- `GET /docs` y `GET /redoc`: Documentación interactiva automática OpenAPI Swagger.

### 1.2 Archivos del Código Fuente
- `app/main.py`: Punto de entrada FastAPI, configuración de prefijo `/api/v1`, registro de `auth_router` y `sleep_records_router`, documentación OpenAPI y middleware de estandarización de errores 422.
- `app/api/routers/auth_router.py`: APIRouter para `/auth/register` y `/auth/login`.
- `app/api/routers/sleep_records_router.py`: APIRouter con endpoints HTTP de registros de sueño protegidos con token de sesión (RNF02).
- `app/api/dependencies.py`: Inyección de dependencias para autenticación (`get_current_user_id` extrayendo UUID de Supabase Auth), repositorios (`get_user_profile_repository`, `get_sleep_record_repository`) y servicios (`get_auth_service`, `get_sleep_record_service`).
- `app/services/auth_service.py`: Capa de lógica de negocio para registro y login con Supabase Auth. Cuenta con modo en memoria activo exclusivamente en entorno de pruebas (`TESTING=true`); en ejecución normal falla de inmediato si faltan credenciales de Supabase.
- `app/services/sleep_record_service.py`: Capa de lógica de negocio para registros de sueño (RN01, RN02, RF04, RF06, RF08) con soporte para UUID de usuario (`id_usuario: str`).
- `app/repositories/user_profile_repository.py`: Capa de persistencia para `perfiles_usuario` en Supabase con RLS. Falla explícitamente si faltan variables en producción.
- `app/repositories/sleep_record_repository.py`: Capa de persistencia para `registros_sueno` en Supabase con claves foráneas UUID hacia `auth.users(id)` y restricción única RN01 (`uq_registros_sueno_usuario_fecha`).
- `app/models/user_profile.py`: Entidad de dominio `PerfilUsuario`.
- `app/models/sleep_record.py`: Entidad de dominio `RegistroSueno` (`id_usuario: str`).
- `app/schemas/auth.py`: DTOs Pydantic v2 para Auth (`RegisterRequest`, `LoginRequest`, `UserProfileResponse`, `AuthResponse`).
- `app/schemas/sleep_record.py`: DTOs Pydantic v2 para registros de sueño con soporte de campos `camelCase` y `snake_case`.
- `app/core/exceptions.py`: Jerarquía de excepciones de dominio (`AuthenticationError`, `UserAlreadyExistsError`, `InvalidTokenError`, `SleepRecordAlreadyExistsError`, `FutureSleepTimeError`, `SleepRecordNotFoundError`, `InvalidSleepDataError`).
- `app/core/config.py`: Configuraciones de sistema, soporte para variable `TESTING=true` y detección de credenciales reales de Supabase.
- `supabase/schema_perfiles_usuario.sql`: Script DDL SQL para tabla `perfiles_usuario` vinculada a `auth.users(id)` con triggers de auditoría y políticas RLS.
- `supabase/migration_registros_sueno_uuid.sql`: Script de migración SQL para adaptar `registros_sueno.id_usuario` a UUID referenciando `auth.users(id)` con RLS.
- `tests/test_auth.py`: Suite de 7 pruebas unitarias y de integración para registro, login, tokens inválidos, 401 sin sesión y fallo de variables en producción.
- `tests/test_sleep_records.py`: Suite de 15 pruebas de dominio y endpoints protegidos, incluyendo prueba de RN01 independiente por usuario.
- `tests/test_sleep_repository.py`: Suite de 5 pruebas unitarias para persistencia y mapeo con UUIDs.

---

## 2. Decisiones Técnicas

1. **Gestión de Identidad y Contraseñas (RNF01, RNF02):**
   - La autenticación y hashing seguro de contraseñas es delegado a **Supabase Auth** (`auth.users`).
   - Las contraseñas nunca se persisten en tablas propias de la aplicación.
   - El UUID emitido por Supabase Auth es la clave primaria de `perfiles_usuario` y la clave foránea de `registros_sueno`.

2. **Modo de Pruebas Seguro:**
   - El modo de pruebas en memoria para `AuthService` y `UserProfileRepository` solo se activa si la variable de entorno `TESTING=true` o `ENVIRONMENT=test` está presente.
   - En ejecución normal, la aplicación no continúa silenciosamente en memoria si faltan variables de Supabase; lanza un error claro al inicializarse.

3. **Restricción RN01 Multi-Usuario:**
   - La restricción única `(id_usuario, fecha)` garantiza que dos usuarios distintos pueden registrar descansos para la misma fecha calendario sin colisión.

---

## 3. Qué Falta por Implementar

Basado estrictamente en los requisitos del informe técnico (`docs/informe3.md`):

### 3.1 Backend (FastAPI + Supabase)
- **Módulo de Usuarios (Endpoints restantes de HU1/RF10):**
  - Endpoints: `GET /api/v1/users/me`, `PUT /api/v1/users/me`, `DELETE /api/v1/users/me` (eliminación de perfil y cuenta en cascada, **RF10**).
- **Módulo de Registros de Sueño (Restante):**
  - Endpoint de eliminación de registro propio (`DELETE /api/v1/sleep-records/{id_registro}`, **RF09**).
  - Listado de registros históricos del usuario (`GET /api/v1/sleep-records`).
- **Módulo de Métricas Semanales (`RF11`–`RF14`, `RN03`, HU2):**
  - Endpoint `GET /api/v1/metrics/weekly` con parámetro opcional `start_date` para navegación entre semanas anteriores (**RF13**).
  - Cálculo de promedio semanal a 1 decimal (**RF11**).
  - Identificación de días críticos comparando horas dormidas contra `metaSueno` personal del usuario o umbral por defecto de 6.0 horas (**RN03**, **RF12**).
  - Detección y respuesta de datos insuficientes (`datos_suficientes: false`, **RF14**).
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
  - Ejecutar scripts DDL (`supabase/schema_perfiles_usuario.sql` y `supabase/migration_registros_sueno_uuid.sql`) en el proyecto en la nube.
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
