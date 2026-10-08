# Convenciones de Código y Reglas de Desarrollo

Este documento define los estándares técnicos, lineamientos de codificación y restricciones explícitas que rigen el proyecto SleepTrack.

---

## 1. Convenciones de Código Backend (Python + FastAPI)

### 1.1 Estilo y Estructura
- **Guía de estilo:** Cumplir con **PEP 8** de forma estricta.
- **Tipado estático:** Uso obligatorio de anotaciones de tipo (`typing` y tipado nativo de Python 3.11+: `int | None`, `list[T]`, `dict[str, Any]`).
- **Nomenclatura:**
  - `snake_case`: Funciones, métodos, variables, nombres de archivos y módulos.
  - `PascalCase`: Clases, excepciones de dominio y esquemas Pydantic.
  - `UPPER_SNAKE_CASE`: Constantes y enumeraciones.
- **Esquemas y DTOs:** Uso de Pydantic v2 para la validación estricta de datos de entrada y salida en la capa de API.
- **Inyección de dependencias:** Utilizar `Depends()` de FastAPI para inyectar servicios, repositorios y validadores de autenticación.

### 1.2 Arquitectura en Capas (Router → Service → Repository)
- **Router:**
  - Solo define la ruta, los códigos de respuesta, las dependencias y la serialización.
  - No ejecuta operaciones SQL ni transformaciones de datos del negocio.
  - Lanza excepciones HTTP (`HTTPException`) mapeadas desde excepciones de dominio.
- **Service:**
  - Encapsula la lógica de negocio y las validaciones de las reglas de negocio (RN01, RN02, RN03, RN04).
  - No contiene referencias a frameworks web (`Request`, `Response`, `HTTPException`).
  - Lanza excepciones de dominio propias (ej. `SleepRecordAlreadyExistsError`, `FutureSleepTimeError`, `DuplicateAlertError`).
- **Repository:**
  - Encapsula las consultas a Supabase / PostgreSQL.
  - Retorna modelos del dominio o diccionarios tipados.
  - No valida reglas de negocio del servicio.

### 1.3 Manejo de Errores y Validaciones
- Toda entrada inválida debe ser rechazada con mensajes de error específicos y descriptivos (en cumplimiento de **RF06**).
- Los errores no controlados en producción deben capturarse y registrarse en logs para monitoreo (en cumplimiento de **RNF06**).
- No ocultar excepciones con bloques `try...except` vacíos (`pass`).

---

## 2. Restricciones Explícitas: Qué NO Hacer

Cualquier código o propuesta que incluya los siguientes elementos será rechazada:

### ❌ 1. Sin Sensores Automáticos
- **Prohibido:** El uso de sensores del dispositivo móvil (acelerómetro, giroscopio, micrófono, podómetro o sensores de luz) para detectar el inicio o fin del sueño.
- **Regla:** **Todo el registro de sueño es 100% manual**, ingresado por el usuario mediante el formulario de la aplicación (hora de acostarse, hora de despertar y calificación de 1 a 5).

### ❌ 2. Sin Inteligencia Artificial (IA / ML)
- **Prohibido:** Modelos de machine learning, redes neuronales, regresiones complejas, LLMs o análisis predictivo para predecir hábitos o calificar el descanso.
- **Regla:** El análisis del descanso es puramente determinista y basado en estadísticas directas y reglas de negocio fijas (cálculo de horas cruzando medianoche según **RF04**, promedio aritmético según **RF11**, y detección de días críticos según umbral de meta o 6 horas según **RN03**).

### ❌ 3. Sin Integración con Wearables ni Hardware Externo
- **Prohibido:** Integración con smartwatches, pulseras deportivas (Apple Watch, Wear OS, Fitbit, Garmin, etc.) o APIs de salud nativas de terceros vinculadas a hardware externo.
- **Regla:** La aplicación solo interactúa con la entrada directa del usuario en su pantalla táctil.

### ❌ 4. Sin Almacenamiento Local como Base de Datos Primaria
- **Prohibido:** Utilizar SQLite, Room, Hive, Realm o almacenamiento en archivos locales en el dispositivo móvil como fuente de persistencia de los registros de sueño.
- **Regla:** La persistencia relacional reside en la nube mediante **Supabase** (PostgreSQL) para garantizar sincronización entre dispositivos e integridad (en cumplimiento de **RNF04**). Los datos no se almacenan localmente para evitar inconsistencias entre dispositivos.

### ❌ 5. Sin Diagnósticos Clínicos ni Médicos
- **Prohibido:** Emitir diagnósticos médicos, detectar patologías clínicas (como apnea obstructiva del sueño o insomnio crónico patológico) o recomendar tratamientos farmacológicos.
- **Regla:** La aplicación es exclusivamente una herramienta de orden y hábitos de higiene del sueño con propósitos educativos y de autocontrol.

### ❌ 6. Sin Integración con Calendarios Externos
- **Prohibido:** Sincronización con Google Calendar, Apple Calendar, Microsoft Outlook u otras plataformas externas de gestión de tiempo.

### ❌ 7. No Inventar Requisitos
- **Prohibido:** Agregar funcionalidades no contempladas en el informe oficial (`docs/informe3.md`) sin validación previa. Si se identifica una ambigüedad o falta de detalle, se debe consultar con el usuario antes de asumir una solución.
