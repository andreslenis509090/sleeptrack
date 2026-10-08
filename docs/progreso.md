# Progreso del Proyecto SleepTrack

Documento de seguimiento del estado del sistema, componentes implementados, decisiones técnicas, pendientes y guías de ejecución.

---

## 1. Qué Quedó Implementado (con Rutas)

Se implementó el backend del **Módulo de Registro de Sueño (HU1)** cumpliendo con los requisitos funcionales **RF03, RF04, RF05, RF06, RF08** y las reglas de negocio **RN01 y RN02**, bajo el patrón en tres capas **Router → Service → Repository**.

### 1.1 Rutas y Endpoints HTTP
- `POST /api/v1/sleep-records`: Crear registro diario de sueño.
  - Valida unicidad de 1 registro por usuario y fecha (**RN01**). Si ya existe, retorna HTTP `409 Conflict` con el ID del registro existente orientando a editarlo (**RF08**).
  - Valida que la hora de acostarse no sea futura contra el reloj en tiempo real (**RN02**, **RF05**). Si es futura, retorna HTTP `400 Bad Request`.
  - Valida campos obligatorios y formato de hora (**RF06**), y calificación en escala 1 a 5 (**RF03**, **RF05**). Si falla, retorna HTTP `422 Unprocessable Entity` o `400 Bad Request`.
  - Calcula automáticamente la duración en horas cruzando medianoche (**RF04**).
  - Retorna confirmación inmediata (**RF08**) con HTTP `201 Created`.
- `GET /api/v1/sleep-records/by-date/{fecha}`: Consulta de existencia de registro para una fecha (permite al cliente móvil detectar duplicados y ofrecer edición previa, **RF08**, **RN01**). Retorna `200 OK` o `404 Not Found`.
- `PUT /api/v1/sleep-records/{id_registro}`: Editar un registro existente para una fecha (**RF08**). Recalcula la duración (**RF04**) y valida hora no futura (**RN02**). Retorna `200 OK`.
- `GET /health`: Endpoint de monitoreo de disponibilidad del backend (**RNF03**).
- `GET /docs` y `GET /redoc`: Documentación interactiva automática OpenAPI Swagger.

### 1.2 Archivos del Código Fuente
- `app/main.py`: Punto de entrada FastAPI, configuración de prefijo `/api/v1`, documentación OpenAPI y middleware de estandarización de errores de validación 422.
- `app/api/routers/sleep_records_router.py`: APIRouter con los endpoints HTTP de registros de sueño, inyección de dependencias y mapeo de excepciones de dominio a códigos de estado HTTP.
- `app/api/dependencies.py`: Inyección de dependencias con `Depends()` para autenticación/sesión (`get_current_user_id`), repositorio (`get_sleep_record_repository`) y servicio (`get_sleep_record_service`).
- `app/services/sleep_record_service.py`: Capa de lógica de negocio pura. Aplica RN01, RN02, orquesta cálculos RF04, valida RF06/RF08 y lanza excepciones de dominio tipadas sin acoplamiento a FastAPI.
- `app/repositories/sleep_record_repository.py`: Capa de persistencia para Supabase (PostgreSQL en la nube). Métodos `get_by_user_and_date`, `get_by_id`, `create` y `update`.
- `app/models/sleep_record.py`: Entidad de dominio `RegistroSueno` con métodos estáticos `calcular_duracion()` (RF04) y `validar_hora_futura()` (RF05, RN02).
- `app/schemas/sleep_record.py`: DTOs Pydantic v2 (`SleepRecordCreate`, `SleepRecordUpdate`, `SleepRecordResponse`, `SleepRecordConflictResponse`, `StandardErrorResponse`) con soporte simultáneo para camelCase y snake_case.
- `app/core/exceptions.py`: Jerarquía de excepciones de dominio (`SleepRecordAlreadyExistsError`, `FutureSleepTimeError`, `SleepRecordNotFoundError`, `InvalidSleepDataError`, `DomainError`).
- `app/core/config.py`: Configuración de variables de entorno (`SUPABASE_URL`, `SUPABASE_KEY`) y fábrica de cliente Supabase.
- `tests/test_sleep_records.py`: Suite de 14 pruebas automatizadas (unitarias y de integración con TestClient).
- `requirements.txt`: Dependencias del proyecto (`fastapi`, `uvicorn`, `pydantic`, `supabase`, `python-dateutil`, `pytest`, `httpx`).

---

## 2. Decisiones Técnicas

1. **Arquitectura Desacoplada (Router → Service → Repository):**
   - El Router no ejecuta lógica de cálculo ni consultas a la base de datos.
   - El Service no utiliza objetos `Request`, `Response` ni lanza `HTTPException`. Utiliza excepciones de dominio tipadas (`SleepRecordAlreadyExistsError`, `FutureSleepTimeError`), preservando la portabilidad del código de negocio.
   - El Repository aísla todas las operaciones de entrada/salida sobre Supabase.

2. **Estrategia de Repositorio y Entorno de Pruebas:**
   - La persistencia oficial en producción es **Supabase (PostgreSQL en la nube)** (RNF04).
   - Para permitir ejecución de pruebas unitarias y de integración ultrarrápidas, deterministas y sin dependencia de conectividad externa a internet o credenciales en CI/CD, `SleepRecordRepository` cuenta con un mecanismo de persistencia fallback en memoria (`_in_memory_db`), el cual se aísla por prueba mediante `dependency_overrides` en `pytest`.

3. **Interoperabilidad de Nomenclatura (camelCase y snake_case):**
   - En Python se utiliza estrictamente `snake_case` (PEP 8).
   - Para garantizar interoperabilidad con clientes móviles (Android/iOS) que envían y esperan campos en `camelCase` (`horaAcostarse`, `horaDespertar`, `duracionHoras`, `idRegistro`), los esquemas Pydantic v2 están configurados con `ConfigDict(populate_by_name=True)` y alias oficiales del informe.

4. **Casos Borde en Reglas de Negocio:**
   - **Misma hora de inicio y fin (RF04):** Si `hora_acostarse == hora_despertar`, la condición `fin <= inicio` interpreta un ciclo completo de descanso de 24.0 horas cruzando medianoche.
   - **Hora en el límite de tiempo real (RN02):** Si la hora de inicio coincide exactamente con el instante actual (`inicio_dt == now`), la validación la acepta (`inicio_dt > now` es falso). Si es posterior por cualquier margen, se rechaza como hora futura.

5. **Exclusiones Mandatarias Aplicadas:**
   - No se implementaron sensores nativos ni acelerómetros (registro 100% manual).
   - No se incluyeron modelos predictivos ni bibliotecas de IA/ML.
   - No se utiliza almacenamiento local (SQLite/Room) como base de datos primaria.
   - No se crearon campos no contemplados en el informe técnico (ej. sin campo de notas).

---

## 3. Qué Falta por Implementar

Basado estrictamente en los requisitos del informe técnico (`docs/informe3.md`):

### 3.1 Backend (FastAPI + Supabase)
- **Módulo de Autenticación y Usuarios (`RF01`, `RF02`, `RF10`, `RNF01`, `RNF02`):**
  - Hash seguro de contraseñas con bcrypt/argon2.
  - Generación y validación de tokens JWT con expiración.
  - Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/users/me`, `PUT /api/v1/users/me`, `DELETE /api/v1/users/me` (eliminación en cascada).
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
  - Creación y migración del esquema relacional DDL en Supabase Cloud (`usuarios`, `registros_sueno`, `alertas`, `auditoria`).

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
