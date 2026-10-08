---
name: dominio-sueno
description: Usar esta skill al consultar, modelar o implementar las entidades del dominio de higiene del sueño, sus atributos, tipos, métodos, relaciones de clases, y para verificar el cumplimiento de los Requisitos Funcionales (RF), Reglas de Negocio (RN) y Requisitos No Funcionales (RNF) con sus IDs oficiales.
---

# Skill: Dominio del Sistema de Higiene del Sueño

Esta skill contiene la definición formal del modelo de dominio, entidades, relaciones, reglas de negocio y requisitos del sistema SleepTrack, extraídos directamente del informe técnico oficial (`docs/informe3.md`).

---

## 1. Entidades del Dominio y Atributos

### 1.1 `Usuario`
Representa a un estudiante o trabajador que registra sus hábitos de sueño (**RF01**, **RF02**).
- **Atributos:**
  - `idUsuario`: `int` (identificador único)
  - `nombre`: `string`
  - `apellido`: `string`
  - `ocupacion`: `string`
  - `email`: `string` (correo electrónico único)
  - `passwordHash`: `string` (contraseña cifrada de forma segura - **RNF01**)
  - `metaSueno`: `float` (meta personal de horas de sueño)
- **Métodos:**
  - `registrarse(): void` (**RF01**)
  - `autenticarse(email: string, pass: string): boolean` (**RF02**)
  - `editarPerfil(): void` (**RF01**)
  - `eliminarCuenta(): void` (**RF10**)

### 1.2 `RegistroSueno`
Representa un evento diario de descanso ingresado manualmente por el usuario (**RF03**–**RF09**).
- **Atributos:**
  - `idRegistro`: `int` (identificador único)
  - `fecha`: `Date` (fecha del evento de sueño)
  - `horaAcostarse`: `Time` (hora de inicio del sueño, formato 12h AM/PM)
  - `horaDespertar`: `Time` (hora final del sueño)
  - `calificacion`: `int` (autopercepción del descanso en escala de 1 a 5)
  - `duracionHoras`: `float` (duración total calculada automáticamente - **RF04**)
- **Métodos:**
  - `calcularDuracion(): float` (**RF04** - calcula duración total considerando cruce de medianoche)
  - `validarHoraFutura(): boolean` (**RF05**, **RN02** - valida contra reloj en tiempo real)
  - `editar(): void` (**RF08**)
  - `eliminar(): void` (**RF09**)

### 1.3 `Alerta`
Representa un recordatorio programable de higiene del sueño (**RF15**–**RF18**, **RN04**).
- **Atributos:**
  - `idAlerta`: `int` (identificador único)
  - `hora`: `Time` (hora programada para la notificación)
  - `tipo`: `TipoAlerta` (`DORMIR` o `DESPERTAR`)
  - `activa`: `boolean` (estado de activación)
- **Métodos:**
  - `programar(): void` (**RF15**)
  - `modificar(nuevaHora: Time): void` (**RF17**)
  - `desactivar(): void` (**RF18** - desactiva sin eliminar registro histórico)
  - `validarDuplicado(): boolean` (**RF16**, **RN04**)

### 1.4 `TipoAlerta` (Enumeración)
- `DORMIR`: Recordatorio nocturno para prepararse para dormir y desconectarse de pantallas.
- `DESPERTAR`: Alarma o aviso de despertar.

### 1.5 `MetricaSemanal`
Resume el desempeño de sueño semanal y marca días críticos (**RF11**–**RF14**, **RN03**).
- **Atributos:**
  - `idMetrica`: `int` (identificador único)
  - `semanaInicio`: `Date` (fecha de inicio de la semana de 7 días)
  - `semanaFin`: `Date` (fecha final de la semana)
  - `promedioHoras`: `float` (promedio semanal mostrado con un solo decimal)
- **Métodos:**
  - `calcularPromedio(): float` (**RF11**)
  - `marcarDiasCriticos(): List<Date>` (**RF12**, **RN03**)

### 1.6 `Administrador`
Usuario con privilegios de gestión y monitoreo del sistema (**RF19**). Hereda de `Usuario`.
- **Atributos adicionales:**
  - `nivelAcceso`: `string`
- **Métodos:**
  - `generarReporteActividad(fechaInicio: Date, fechaFin: Date): ReporteActividad` (**RF19**)
  - `depurarRegistro(idRegistro: int): void` (**RF19**)
  - `exportarRespaldo(): RespaldoDatos` (**RF19**)

### 1.7 `ReporteActividad`
Reporte estadístico generado por el administrador por rango de fechas (**RF19**).
- **Atributos:**
  - `idReporte`: `int`
  - `fechaInicio`: `Date`
  - `fechaFin`: `Date`
  - `resumenEstadistico`: `string`
- **Métodos:**
  - `generar(): void`

### 1.8 `RespaldoDatos`
Exportación cifrada de la información del sistema (**RF19**).
- **Atributos:**
  - `idRespaldo`: `int`
  - `fechaGeneracion`: `DateTime`
  - `archivoCifrado`: `string`
- **Métodos:**
  - `exportar(): void`

---

## 2. Relaciones de Clases y Cardinalidades

| Relación | Tipo | Cardinalidad | Significado |
| :--- | :--- | :--- | :--- |
| **Administrador → Usuario** | Herencia | — | `Administrador` es una especialización de `Usuario`, hereda sus atributos y operaciones básicas. |
| **Usuario — RegistroSueño** | Composición | `1` — `0..*` | Los registros de sueño no existen sin el usuario que los posee; se eliminan en cascada con la cuenta (**RF10**). |
| **Usuario — Alerta** | Composición | `1` — `0..*` | Las alertas dependen exclusivamente del usuario que las configuró. |
| **Usuario — MétricaSemanal** | Asociación | `1` — `0..*` | Cada usuario genera sus propias métricas semanales calculadas. |
| **MétricaSemanal — RegistroSueño** | Agregación | `1` — `1..7` | Una métrica resume de 1 a 7 registros, pero éstos existen independientemente de la métrica. |
| **Administrador — ReporteActividad** | Asociación | `1` — `0..*` | Un administrador puede generar múltiples reportes de actividad por rangos de fechas. |
| **Administrador — RespaldoDatos** | Asociación | `1` — `0..*` | Un administrador puede generar múltiples respaldos de datos cifrados. |

---

## 3. Requisitos Funcionales (RF) con IDs

- **RF01:** El sistema debe permitir a los usuarios registrarse creando un perfil (nombre, apellido, ocupación, meta de sueño, credenciales).
- **RF02:** El sistema debe permitir la autenticación de usuarios mediante correo electrónico y contraseña.
- **RF03:** El sistema debe permitir registrar un evento de sueño diario, indicando hora de acostarse, hora de despertar, fecha y calificación del descanso (escala 1-5).
- **RF04:** El sistema debe calcular automáticamente la duración total del sueño a partir de la hora de inicio y la hora final, incluyendo los casos donde el sueño cruza la medianoche.
- **RF05:** El sistema debe validar la hora de inicio de sueño ingresada por el usuario, aplicando la restricción definida en **RN02**.
- **RF06:** El sistema debe rechazar registros con campos obligatorios vacíos o formato de hora inválido, informando al usuario el error específico.
- **RF08:** El sistema debe permitir al usuario editar el registro de sueño ya existente para la fecha actual en lugar de crear un duplicado, cuando intente registrar un segundo evento el mismo día, en cumplimiento de **RN01**.
- **RF09:** El sistema debe permitir a los usuarios eliminar sus propios registros de sueño.
- **RF10:** El sistema debe permitir a los usuarios eliminar su propia cuenta, junto con todos los datos asociados.
- **RF11:** El sistema debe calcular y mostrar un resumen semanal de horas dormidas por día, junto con el promedio semanal.
- **RF12:** El sistema debe marcar visualmente como días críticos aquellos días que cumplan la condición definida en **RN03**.
- **RF13:** El sistema debe permitir navegar entre semanas anteriores para consultar el historial de métricas.
- **RF14:** El sistema debe informar al usuario cuando no existan datos suficientes para generar las métricas semanales.
- **RF15:** El sistema debe permitir configurar alertas de higiene del sueño, especificando una hora y un tipo (dormir/despertar).
- **RF16:** El sistema debe validar la configuración de una alerta nueva, aplicando la restricción definida en **RN04**.
- **RF17:** El sistema debe permitir modificar la hora de una alerta existente.
- **RF18:** El sistema debe permitir desactivar una alerta sin eliminar su registro histórico.
- **RF19:** El sistema debe proporcionar una consola administrativa con reportes de actividad, depuración de registros y exportación de respaldos de datos.

---

## 4. Reglas de Negocio (RN) con IDs

- **RN01:** **Solo se permite un registro de sueño por usuario por fecha.** Si el usuario intenta guardar un segundo registro para la misma fecha, el sistema debe bloquear la creación y ofrecer editar el existente (**RF08**).
- **RN02:** **No se puede registrar una hora de inicio de sueño que corresponda a una fecha/hora futura.** La validación se realiza contra el reloj en tiempo real.
- **RN03:** **Un día se considera crítico cuando las horas dormidas registradas son inferiores a la meta de sueño personal definida por el usuario en su perfil (RF01); si el usuario no ha definido una meta, se aplica un umbral por defecto de 6 horas.**
- **RN04:** **No se permite la creación de alertas duplicadas (misma hora y mismo tipo) para un mismo usuario.**

---

## 5. Requisitos No Funcionales (RNF) con IDs

- **RNF01 (Seguridad):** Las contraseñas de los usuarios deben almacenarse cifradas mediante un algoritmo cifrado seguro.
- **RNF02 (Seguridad):** El acceso a los endpoints que gestionan datos personales debe requerir autenticación mediante una sesión con expiración.
- **RNF03 (Disponibilidad):** El backend debe estar desplegado, accesible desde cualquier lugar y en cualquier momento.
- **RNF04 (Persistencia):** Los datos deben almacenarse en una base de datos relacional (Supabase / PostgreSQL en la nube), para garantizar integridad y sincronización entre dispositivos.
- **RNF05 (Usabilidad):** El registro de un evento de sueño debe requerir el menor número de interacciones posible.
- **RNF06 (Monitoreo):** Los errores no controlados en producción deben registrarse.
- **RNF07 (Mantenibilidad):** El código debe organizarse por rutas/endpoints, permitiendo agregar funcionalidades sin afectar las existentes.
- **RNF08 (Rendimiento):** El cálculo de métricas semanales no debe degradar el rendimiento del sistema para otros usuarios conforme crece el volumen de datos.
- **RNF09 (Compatibilidad):** La aplicación debe funcionar en versiones recientes de Android e iOS, y en navegadores web modernos.
