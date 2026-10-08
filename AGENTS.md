# AGENTS.md - Sistema de Monitoreo de Higiene del Sueño

Guía de referencia para agentes de inteligencia artificial y desarrolladores que interactúen con este repositorio.

---

## 1. Resumen del Proyecto

**SleepTrack** es una aplicación móvil de higiene del sueño dirigida a estudiantes y trabajadores con horarios irregulares. El objetivo principal es proporcionar un mecanismo sencillo para registrar, monitorear y analizar los hábitos de descanso diarios, transformando registros subjetivos en estadísticas útiles que permitan identificar patrones de descanso y días críticos, sin depender de la memoria del usuario.

### Actores del Sistema
1. **Usuario Final (Estudiante o Trabajador):** Registra eventos de sueño diarios (horas y autopercepción 1-5), consulta gráficas y métricas semanales con detección de días críticos, y configura alertas recordatorias de higiene del sueño.
2. **Administrador:** Accede a la consola de gestión para monitorear el uso de la aplicación mediante reportes estadísticos por rango de fechas, depurar registros erróneos y exportar respaldos cifrados del sistema.

---

## 2. Stack Tecnológico

- **Backend:** Python 3.11+ con **FastAPI**.
  - Servidor asíncrono ASGI (Uvicorn).
  - Validación de esquemas y tipos con **Pydantic v2**.
  - Documentación interactiva automática (OpenAPI / Swagger en `/docs`).
- **Base de Datos:** **Supabase** (PostgreSQL en la nube).
  - Persistencia relacional para garantizar integridad referencial, consistencia y sincronización entre múltiples dispositivos (RNF04).
  - **IMPORTANTE:** Toda la persistencia reside en la nube con Supabase. **NO se utiliza almacenamiento local** (SQLite, Room, SharedPreferences persistentes, etc.) como fuente de verdad.
- **Autenticación y Seguridad:**
  - Cifrado seguro de contraseñas mediante hashing resistente (RNF01).
  - Manejo de sesiones y tokens con expiración para el acceso a endpoints que gestionan datos personales (RNF02).
- **Cliente:**
  - Aplicación móvil compatible con versiones recientes de Android e iOS, y navegadores web modernos (RNF09).

---

## 3. Arquitectura del Backend

El backend en FastAPI sigue estrictamente el patrón en tres capas: **Router → Service → Repository**.

```
Cliente (App Móvil / Web)
       │
       ▼
┌─────────────────────────┐
│         Router          │  FastAPI APIRouter: Endpoints HTTP, dependencias,
│   (app/api/routers/)    │  validación de request/response con Pydantic Schemas.
└───────────┬─────────────┘
            │ invoca
            ▼
┌─────────────────────────┐
│         Service         │  Lógica de Negocio: Reglas de negocio (RN01 - RN04),
│    (app/services/)      │  cálculos (duración cruzando medianoche RF04, promedios RF11).
└───────────┬─────────────┘
            │ invoca
            ▼
┌─────────────────────────┐
│       Repository        │  Acceso a Datos: Consultas, inserciones, actualizaciones
│   (app/repositories/)   │  y eliminaciones sobre la base de datos Supabase.
└───────────┬─────────────┘
            │ ejecuta SQL / Supabase Client
            ▼
┌─────────────────────────┐
│   Supabase PostgreSQL   │  Base de datos relacional en la nube.
└─────────────────────────┘
```

### Responsabilidades por Capa:

1. **Router (`app/api/routers/`):**
   - Define las rutas HTTP (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
   - Declara los esquemas Pydantic para los cuerpos de petición y respuesta.
   - Realiza la inyección de dependencias (ej. sesión de usuario autenticado, servicio correspondiente).
   - Traduce excepciones de negocio a códigos de estado HTTP estándar (`200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `422`).
   - **Prohibido:** Contener lógica de negocio compleja o invocar directamente a los repositorios o cliente de base de datos.

2. **Service (`app/services/`):**
   - Contiene la lógica del dominio y la aplicación estricta de las reglas de negocio:
     - **RN01:** Validar unicidad de 1 registro por usuario y fecha.
     - **RN02:** Validar que la hora de inicio de sueño no sea futura.
     - **RN03:** Determinar días críticos comparando horas dormidas con la meta de sueño (o 6 horas por defecto).
     - **RN04:** Validar que no existan alertas duplicadas (misma hora y tipo).
     - **RF04:** Cálculo de duración en horas cruzando medianoche.
     - **RF11:** Cálculo de promedios semanales con 1 decimal.
   - Orquesta llamadas a los repositorios y lanza excepciones de dominio tipadas.
   - **Prohibido:** Manipular directamente solicitudes HTTP o responses.

3. **Repository (`app/repositories/`):**
   - Encapsula todas las operaciones con Supabase / PostgreSQL.
   - Maneja filtros por usuario (`id_usuario`), rangos de fechas y operaciones CRUD.
   - Transforma los registros de base de datos en modelos del dominio.

---

## 4. Reglas Generales para Agentes

1. **Fidelidad al Informe:** No inventar entidades, campos ni reglas de negocio. Todas las decisiones de diseño deben basarse en `docs/informe3.md`. Si se requiere una definición no contemplada en el informe, **preguntar al usuario antes de asumir**.
2. **Exclusiones Mandatarias:**
   - **SIN SENSORES:** El registro es 100% manual. No proponer ni implementar uso de acelerómetro, micrófono ni sensores nativos.
   - **SIN INTELIGENCIA ARTIFICIAL:** No incluir modelos predictivos ni IA para el análisis de sueño. Toda la lógica es determinista y basada en reglas (RN01–RN04).
   - **SIN HARDWARE EXTERNO / WEARABLES:** No implementar integración con smartwatches ni pulseras de actividad.
   - **SIN ALMACENAMIENTO LOCAL COMO BASE DE DATOS:** La persistencia es exclusivamente en la nube con Supabase.
   - **SIN DIAGNÓSTICOS CLÍNICOS:** El sistema es una herramienta de orden y hábitos, no un dispositivo médico.
   - **SIN CALENDARIOS EXTERNOS:** No sincronizar con Google Calendar ni calendarios de terceros.
3. **Identificadores Oficiales:** Utilizar siempre los IDs oficiales del informe al documentar o comentar código:
   - Requisitos Funcionales: `RF01` al `RF19`.
   - Reglas de Negocio: `RN01` al `RN04`.
   - Requisitos No Funcionales: `RNF01` al `RNF09`.
   - Historias de Usuario: `HU1` al `HU4`.
4. **Flujo de Trabajo y Progreso:** Al iniciar, lee `docs/progreso.md`. Al terminar cada tarea, actualízalo.

