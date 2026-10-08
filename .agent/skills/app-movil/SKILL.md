---
name: app-movil
description: Usar esta skill para diseñar, implementar, maquetar y validar las pantallas, componentes de interfaz de usuario, flujos de interacción (principal y alternativo), criterios de aceptación y casos de prueba para las Historias de Usuario HU1 a HU4 de la aplicación móvil de higiene del sueño.
---

# Skill: Aplicación Móvil (Pantallas y Flujos de HU1 a HU4)

Esta skill documenta las especificaciones de interfaz de usuario, interacción, validaciones del cliente, criterios de aceptación (Given/When/Then), casos de prueba y condiciones especiales para las cuatro historias de usuario del sistema SleepTrack, extraídas estrictamente de `docs/informe3.md`.

---

## 1. HU1: Registro de Inicio de Sueño

### 1.1 Definición
*Como usuario, quiero registrar mi hora de dormir para llevar un control de mis hábitos de descanso.*

- **Actor:** Usuario final (estudiante o trabajador).
- **Precondición:** El usuario tiene la aplicación instalada, abierta y con sesión activa.
- **Postcondición:** El registro queda almacenado en la base de datos en la nube (Supabase), asociado al usuario autenticado.

### 1.2 Pantalla: Formulario de Registro de Sueño (`SleepRecordScreen`)
- **Componentes de UI:**
  - **Selector de Fecha:** Campo de selección de fecha (por defecto: fecha actual).
  - **Selector de Hora de Acostarse:** Input con TimePicker en **formato de 12 horas con indicador AM/PM**.
  - **Selector de Hora de Despertar:** Input con TimePicker en **formato de 12 horas con indicador AM/PM**.
  - **Calificación del Descanso:** Selector visual de autopercepción en escala del **1 al 5** (estrellas o selector de satisfacción).
  - **Botón "Guardar":** Dispara la validación y el envío.
  - **Botón "Cancelar" / "Volver":** Cancela la operación sin persistir datos.

### 1.3 Flujos de Interacción
- **Flujo Principal:**
  1. El usuario navega a la pantalla de registro de sueño.
  2. Selecciona la hora en que se acostó y la hora de despertar.
  3. Califica cómo se siente al despertar en una escala del 1 al 5.
  4. Presiona el botón "Guardar".
  5. El sistema valida que los datos estén completos, sin horas futuras y en formato correcto.
  6. Se almacena el registro en la base de datos en la nube y se muestra un mensaje de confirmación exitosa.
- **Flujos Alternativos:**
  - **Campo de hora vacío:** El sistema resalta el campo en rojo y muestra el mensaje: `"La hora es obligatoria"`.
  - **Formato inválido:** Si el usuario ingresa texto no numérico o inválido, bloquea la entrada o muestra alerta `"Formato de hora no válido"`.
  - **Hora futura (RN02):** Si la hora seleccionada es mayor a la hora actual del dispositivo en tiempo real, bloquea el guardado y notifica: `"No se puede registrar un inicio de sueño en el futuro"`.
  - **Registro existente para la misma fecha (RN01 / RF08):** Si ya existe un registro para esa fecha, el sistema informa que ya existe un registro y ofrece redirigir a editarlo (**RF08**) en lugar de crear un duplicado.
  - **Cancelación:** Si pulsa "Cancelar" o "Volver", regresa a la pantalla principal sin guardar ningún dato.

### 1.4 Criterios de Aceptación (Escenarios)

| Escenario | Given | When | Then |
| :--- | :--- | :--- | :--- |
| **Registro exitoso de hora de descanso** | El usuario se encuentra en el formulario de "Inicio de Sueño" | Ingresa una hora válida y pulsa "Guardar" | El sistema almacena el registro y muestra un mensaje de confirmación exitosa |
| **Intento de registro con campos vacíos** | El usuario abrió el formulario de registro | Deja el campo de hora vacío y pulsa el botón "Guardar" | El sistema resalta el campo en rojo y muestra el mensaje "La hora es obligatoria" |
| **Validación de formato de hora incorrecto** | El usuario intenta ingresar un dato manualmente | Escribe un texto que no corresponde a una hora | El sistema bloquea la entrada o muestra una alerta de "Formato de hora no válido" |
| **Registro de una hora futura** | El usuario está registrando su descanso actual | Selecciona una hora mayor a la hora actual del dispositivo | El sistema impide el guardado y notifica que "No se puede registrar un inicio de sueño en el futuro" |
| **Edición de un registro existente del mismo día** | El usuario ya registró su sueño hoy y vuelve a abrir el formulario | Intenta guardar un segundo registro para la misma fecha | El sistema le informa que ya existe un registro y lo redirige a editarlo (RF08), en lugar de crear un duplicado |
| **Cancelación del registro** | El usuario ingresó una hora en el formulario | Decide pulsar el botón "Cancelar" o "Volver" | El sistema regresa a la pantalla principal sin guardar ningún dato en la base de datos |

### 1.5 Casos de Prueba

| # | Caso de prueba | Resultado esperado |
| :-: | :--- | :--- |
| **1** | El usuario ingresa una hora válida y presiona el botón "Guardar" | El sistema almacena el dato correctamente y muestra un mensaje de confirmación exitosa |
| **2** | El usuario deja el campo de hora vacío y presiona el botón "Guardar" | El sistema impide el guardado, resalta el campo y muestra un mensaje de advertencia |
| **3** | El usuario intenta registrar una hora que aún no ha ocurrido (hora futura) | El sistema bloquea la acción y notifica que no se puede registrar un sueño posterior a la hora actual |
| **4** | El usuario ingresa una hora y luego presiona el botón "Cancelar" | El sistema cierra el formulario sin guardar ningún dato y regresa a la pantalla de inicio |
| **5** | El usuario intenta guardar un segundo registro para una fecha que ya tiene uno | El sistema le informa que ya existe un registro para esa fecha y ofrece editarlo (RF08) |

### 1.6 Condiciones Especiales de HU1
- La hora debe manejarse en **formato de 12 horas con indicador AM/PM**.
- El sistema debe validar la entrada contra el **reloj en tiempo real** del dispositivo.
- Solo se permite **un registro de sueño por fecha**; si intenta guardar un segundo registro, el sistema informa y ofrece editarlo (**RF08**).

---

## 2. HU2: Visualización de Métricas Semanales

### 2.1 Definición
*Como usuario, quiero ver una gráfica de barras semanal para identificar mis días críticos de mal descanso.*

- **Actor:** Usuario final (estudiante o trabajador).
- **Precondición:** El usuario tiene al menos un registro de sueño guardado.
- **Postcondición:** El usuario puede identificar visualmente sus días críticos de mal descanso.

### 2.2 Pantalla: Dashboard de Estadísticas Semanales (`WeeklyMetricsScreen`)
- **Componentes de UI:**
  - **Selector/Navegador de Semanas:** Flechas de navegación `< Semana Anterior` y `Semana Siguiente >` (**RF13**).
  - **Gráfica de Barras:**
    - 7 columnas correspondientes a los días de la semana.
    - Eje Y con escala autodescalable según la duración máxima registrada.
    - Barras normales para días con sueño suficiente.
    - **Barras resaltadas en color rojo** para los días críticos identificados según **RN03**.
  - **Promedio Semanal:** Indicador numérico destacado que muestra el promedio de horas dormidas **con un solo decimal** (ejemplo: `7.5 horas`).
  - **Estado Vacío / Sin Datos Suficientes:** Mensaje informativo: `"Registra al menos un día para ver tus estadísticas"` / `"No hay datos suficientes para mostrar"` (**RF14**).
  - **Alerta de Conexión:** Banner de error si falla la sincronización con el servidor: `"No se pudo cargar la información, verifica tu conexión"`.

### 2.3 Flujos de Interacción
- **Flujo Principal:**
  1. El usuario accede al módulo de estadísticas.
  2. El sistema recupera los registros de los últimos 7 días desde la base de datos en la nube.
  3. Genera una gráfica de barras con las horas dormidas por día.
  4. Muestra el promedio semanal con un solo decimal.
  5. Resalta en color rojo los días con horas dormidas por debajo de la meta personal (o < 6 horas si no definió meta).
  6. El usuario puede pulsar la flecha de navegación para consultar semanas anteriores.
- **Flujos Alternativos:**
  - **Sin registros en la semana:** Muestra gráfica vacía y el mensaje informativo correspondiente (**RF14**).
  - **Fallo de conexión:** Muestra mensaje de error de conexión invitando a verificar la red.

### 2.4 Criterios de Aceptación (Escenarios)

| Escenario | Given | When | Then |
| :--- | :--- | :--- | :--- |
| **Visualización con datos suficientes** | El usuario ha registrado al menos 7 días de sueño en la semana actual | Selecciona la opción "Ver Gráfica Semanal" | El sistema genera una gráfica de barras mostrando las horas dormidas por día y calcula el promedio semanal |
| **Visualización con datos insuficientes** | El usuario es nuevo o no tiene registros en la semana actual | Accede al módulo de métricas | El sistema muestra una gráfica vacía y un mensaje informativo "Registra al menos un día para ver tus estadísticas" |
| **Filtrado por semana anterior** | El usuario desea ver su historial pasado | Selecciona la flecha de navegación "Semana Anterior" | El sistema actualiza la gráfica con los datos históricos almacenados en la base de datos de forma inmediata |
| **Identificación visual de días críticos** | El usuario definió una meta personal de sueño de 8 horas en su perfil (RF01) | El sistema detecta un día con horas dormidas por debajo de esa meta personal | El sistema resalta esa barra con color rojo para alertar sobre el mal descanso |
| **Identificación de días críticos sin meta definida** | El usuario no definió una meta personal de sueño | El sistema detecta un día con menos de 6 horas registradas (umbral por defecto) | El sistema resalta esa barra con color rojo para alertar sobre el mal descanso |
| **Error de conexión al cargar datos** | Los datos se sincronizan con un servidor externo | El usuario intenta cargar las métricas sin conexión a internet | El sistema muestra un mensaje de error "No se pudo cargar la información, verifica tu conexión" |

### 2.5 Casos de Prueba

| # | Caso de prueba | Resultado esperado |
| :-: | :--- | :--- |
| **1** | El usuario accede al módulo de estadísticas teniendo registros de los últimos 7 días | El sistema genera y muestra una gráfica de barras con el resumen de horas dormidas por día |
| **2** | El usuario intenta ver la gráfica sin haber realizado ningún registro previo | El sistema muestra la interfaz de gráficas vacía con un mensaje: "No hay datos suficientes para mostrar" |
| **3** | El sistema detecta un día con horas dormidas por debajo de la meta personal del usuario (o de 6 horas si no la definió) | El sistema resalta la barra correspondiente en color rojo para alertar sobre el bajo descanso |
| **4** | El usuario selecciona la opción de navegar a la "Semana Anterior" | El sistema carga y visualiza correctamente los datos históricos de la semana previa |

### 2.6 Condiciones Especiales de HU2
- Los promedios de sueño deben mostrarse **con un solo decimal** (ejemplo: `7.5 horas`).
- La gráfica debe ser **autodescalable según la duración máxima registrada**.
- El color **rojo** de alerta se activa cuando las horas dormidas están por debajo de la meta personal definida en su perfil (**RF01**); si no definió una meta, se usa el **umbral por defecto de 6 horas** (**RN03**).

---

## 3. HU3: Programación de Recordatorios de Higiene de Sueño

### 3.1 Definición
*Como usuario, quiero programar una notificación para prepararme para dormir y desconectarme de las pantallas a tiempo.*

- **Actor:** Usuario final (estudiante o trabajador).
- **Precondición:** El usuario tiene la aplicación instalada y ha otorgado permisos de notificación.
- **Postcondición:** El recordatorio queda activo y persiste incluso si el dispositivo se reinicia.

### 3.2 Pantalla: Configuración de Recordatorios (`AlertSettingsScreen`)
- **Componentes de UI:**
  - **Interruptor General:** Switch maestro para activar o desactivar todas las notificaciones de la aplicación.
  - **Selector de Tipo de Alerta:** Selector de opciones:
    - `"dormir"`: Recordatorio nocturno para iniciar rutina y desconectarse de pantallas.
    - `"despertar"`: Alerta matutina.
  - **Selector de Hora:** TimePicker en formato de 12 horas AM/PM.
  - **Botón "Guardar Configuración":** Programa la alerta en el backend y en el programador de notificaciones locales del SO.
  - **Lista de Alertas Programadas:** Listado con hora, tipo y switch individual para activar/desactivar sin eliminar (**RF18**), y opción de editar hora (**RF17**).

### 3.3 Flujos de Interacción
- **Flujo Principal:**
  1. El usuario activa el interruptor de recordatorios.
  2. Elige el tipo de alerta (`dormir` o `despertar`).
  3. Selecciona una hora específica.
  4. Guarda la configuración.
  5. El sistema valida que no exista una alerta duplicada (misma hora y mismo tipo - **RN04**).
  6. El sistema programa la notificación. A la hora exacta, el dispositivo emite la alerta visual y sonora, incluso con la app cerrada.
- **Flujos Alternativos:**
  - **Desactivación general:** Si desactiva el interruptor general, se cancelan todas las alertas programadas del sistema operativo.
  - **Modificación de hora:** Si el usuario edita la hora de una alerta existente, cancela la anterior y reprograma la nueva inmediatamente (**RF17**).
  - **Alerta duplicada (RN04):** Si intenta configurar una alerta idéntica en hora y tipo a una existente, el sistema bloquea y notifica el error.

### 3.4 Criterios de Aceptación (Escenarios)

| Escenario | Given | When | Then |
| :--- | :--- | :--- | :--- |
| **Activación exitosa del recordatorio de dormir** | El usuario activó el interruptor de "Recordatorio Nocturno" | Selecciona una hora específica y guarda la configuración | El sistema programa una notificación de tipo "dormir" para esa hora exacta |
| **Activación exitosa del recordatorio de despertar** | El usuario desea configurar una alerta para despertarse | Selecciona el tipo "despertar", define una hora y guarda la configuración | El sistema programa una notificación de tipo "despertar" para esa hora exacta |
| **Recepción de la notificación en segundo plano** | La aplicación no está abierta, pero sigue en ejecución | El reloj del dispositivo llega a la hora programada | El sistema lanza una alerta visual y de sonido con el mensaje correspondiente al tipo de alerta |
| **Modificación de una hora ya existente** | Ya existe un recordatorio activo | El usuario cambia la hora | El sistema cancela la alerta anterior y reprograma la nueva notificación inmediatamente |
| **Desactivación total de alertas** | El usuario tiene recordatorios activos | Apaga el interruptor general de notificaciones en la aplicación | El sistema elimina todas las alertas programadas del sistema operativo |
| **Persistencia tras reinicio del dispositivo** | El usuario tiene un recordatorio configurado | El dispositivo se apaga y se vuelve a encender | La aplicación debe asegurar que la notificación siga programada sin necesidad de abrir la aplicación manualmente |

### 3.5 Casos de Prueba

| # | Caso de prueba | Resultado esperado |
| :-: | :--- | :--- |
| **1** | El usuario configura una alerta de tipo "dormir" a las 9:00 PM y guarda la configuración | El sistema programa una notificación que se activará exactamente a la hora definida |
| **2** | El usuario configura una alerta de tipo "despertar" a las 6:30 AM y guarda la configuración | El sistema programa una notificación de despertar que se activará exactamente a la hora definida |
| **3** | El dispositivo llega a la hora programada con la aplicación cerrada | El sistema lanza una notificación visual y sonora recordando al usuario iniciar su rutina de sueño o despertar |
| **4** | El usuario desactiva el interruptor de recordatorios en el menú de ajustes | El sistema elimina todas las alertas programadas y deja de enviar notificaciones |
| **5** | El usuario cambia la hora de una alerta existente de 10:00 PM a 9:30 PM | El sistema sobrescribe la alerta anterior y confirma la actualización del nuevo horario |

### 3.6 Condiciones Especiales de HU3
- La aplicación debe solicitar y tener activados los **permisos de notificación** del sistema operativo móvil.
- Las alertas deben sonar incluso si el teléfono está en modo "No molestar" (siempre que el usuario lo autorice).
- El sistema debe evitar la programación de **dos alertas idénticas (misma hora y mismo tipo)** para el mismo usuario (**RN04**).

---

## 4. HU4: Gestión y Monitoreo del Sistema (Consola Administrativa)

### 4.1 Definición
*Como Administrador del sistema, quiero acceder a una consola de gestión y reportes, para monitorear el uso de la aplicación y asegurar la integridad de los datos de los usuarios.*

- **Actor:** Administrador del sistema.
- **Precondición:** El administrador tiene credenciales válidas.
- **Postcondición:** Todas las acciones del administrador quedan registradas en un archivo de auditoría.

### 4.2 Pantalla: Consola Administrativa (`AdminDashboardScreen`)
- **Componentes de UI:**
  - **Login Administrativo:** Formulario de acceso protegido por credenciales.
  - **Módulo de Reportes de Actividad:**
    - Selectores de fecha de inicio y fecha de fin.
    - Botón "Generar Reporte".
    - Panel de visualización de resumen estadístico de uso (usuarios activos, volumen de registros, etc.).
  - **Módulo de Depuración Manual de Registros:**
    - Listado o buscador de registros por ID o usuario.
    - Botón "Eliminar Registro" con **modal de confirmación que incluya mensaje de advertencia obligatorio**.
  - **Módulo de Respaldo de Datos:**
    - Botón "Exportar Respaldo de Seguridad".
    - Descarga de archivo cifrado con la información del sistema.

### 4.3 Flujos de Interacción
- **Flujo Principal:**
  1. El administrador ingresa sus credenciales válidas e inicia sesión.
  2. Accede al panel administrativo.
  3. Puede solicitar un reporte de actividad seleccionando un rango de fechas.
  4. Puede depurar registros erróneos (eliminándolos tras confirmación).
  5. Puede exportar un respaldo de seguridad cifrado.
  6. Todas las acciones se registran en el log de auditoría.
- **Flujos Alternativos:**
  - **Credenciales incorrectas:** El sistema deniega el acceso y registra el intento fallido en el log de seguridad (**RNF06**).

### 4.4 Criterios de Aceptación (Escenarios)

| Escenario | Given | When | Then |
| :--- | :--- | :--- | :--- |
| **Generación de reportes de actividad** | El administrador ha iniciado sesión en el panel de control | Selecciona un rango de fechas y solicita el reporte de actividad | El sistema procesa los datos y despliega el resumen estadístico de uso |
| **Depuración manual de registros** | Se ha identificado un registro de usuario con información errónea | El administrador utiliza la función de borrado manual | El sistema elimina el registro de la base de datos y confirma la operación |
| **Validación de seguridad en el login** | El administrador intenta acceder a la consola de gestión | Ingresa una contraseña que no coincide con los registros | El sistema deniega el acceso y registra el intento fallido en el log |
| **Respaldo de seguridad de la base de datos** | El administrador requiere un respaldo de la información del sistema | Activa la función de exportación de datos | El sistema genera un archivo descargable con toda la información cifrada |

### 4.5 Casos de Prueba

| # | Caso de prueba | Resultado esperado |
| :-: | :--- | :--- |
| **1** | El administrador inicia sesión en el panel de control, define un rango de fechas específico y solicita el reporte de actividad | El sistema procesa los registros y despliega un resumen estadístico |
| **2** | El administrador identifica un registro de usuario con información errónea y utiliza la función de borrado manual | El sistema elimina el registro de la base de datos |
| **3** | El administrador intenta acceder a la consola de gestión ingresando una contraseña que no coincide con los registros | El sistema niega el acceso |
| **4** | El administrador activa la función de exportación de datos para realizar un respaldo de seguridad | El sistema genera un archivo descargable |

### 4.6 Condiciones Especiales de HU4
- El acceso al panel administrativo debe requerir **obligatoriamente una autenticación** previa.
- El sistema debe **registrar cada acción del administrador en un archivo de auditoría**.
- La generación de reportes masivos **no debe afectar el rendimiento de la aplicación** para los usuarios finales (**RNF08**).
- La eliminación de datos de usuario debe solicitar una **confirmación con una advertencia**.
