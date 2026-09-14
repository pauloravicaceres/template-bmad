## 1. RESUMEN DE DISEÑO

- **Historia Base:** Reserva e Integración de Citas Podológicas en Tiempo Real
- **Enfoque de Usabilidad:** Se diseñó un flujo de reserva ágil e intuitivo que calcula dinámicamente la duración total acumulada de los servicios podológicos seleccionados y valida la disponibilidad continua del especialista en tiempo real, omitiendo por completo cualquier costo o tarifa monetaria.



## 2. MAPA DE ESTADOS VISUALES

*Por cada escenario de la HU, documenta el entregable visual híbrido.*

### Estado 1: Selección y Reserva Exitosa de Cita Podológica (Happy Path)
**Escenario cubierto:** Escenario 1: Reserva exitosa de cita con profesional y múltiples servicios (Happy Path)
**ID de Pantalla en Stitch:** `projects/12386224423209721294/screens/cd3635f99991499a91cfec626e4ad361`
**Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  [LOGO] SPA PODOLÓGICO ÁMELY      [Inicio]  [Servicios]  [Especialistas]  [Contacto] |
+-----------------------------------------------------------------------------------+
|  RESERVA DE CITA PODOLÓGICA EN TIEMPO REAL                                        |
|  [Pill: Reserva Directa - Atenciones Especializadas]                              |
|                                                                                   |
|  PASO 1: SELECCIONE SERVICIOS PODOLÓGICOS                                         |
|  +-----------------------------------------------------------------------------+  |
|  | [X] Quiropodia Completa                 | Duración estimada: 45 min           |  |
|  | [X] Tratamiento Láser para Micosis      | Duración estimada: 30 min           |  |
|  | [ ] Eval. Biomecánica de la Pisada      | Duración estimada: 45 min           |  |
|  +-----------------------------------------------------------------------------+  |
|  Duración Total Acumulada: [ 75 minutos ]                                         |
|                                                                                   |
|  PASO 2: SELECCIONE SU PODÓLOGO ESPECIALISTA                                      |
|  (o) Lic. Carmen Silva (Podóloga Senior)   ( ) Lic. Roberto Gómez (Especialista)   |
|                                                                                   |
|  PASO 3: SELECCIONE FECHA Y BLOQUE DE TIEMPO CONTINUO DISPONIBLE (75 min)        |
|  Fecha: [ 15/09/2026 v ]                                                          |
|  +-------------------+  +-------------------+  +-------------------+              |
|  | 09:00 - 10:15     |  | 10:15 - 11:30     |  | 14:00 - 15:15     |              |
|  | [ SELECCIONADO ]  |  | [ DISPONIBLE ]    |  | [ DISPONIBLE ]    |              |
|  +-------------------+  +-------------------+  +-------------------+              |
|                                                                                   |
|  DATOS DEL PACIENTE:                                                              |
|  Nombre: [ Juan Pérez           ]  Teléfono/WhatsApp: [ +51 987654321        ]  |
|  Correo: [ juan.perez@email.com ]                                                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | [ CONFIRMAR Y BLOQUEAR MI CITA ]  (Sin costos ni cobros en línea)           |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```
**Nota de Interfaz:** El botón "CONFIRMAR Y BLOQUEAR MI CITA" permanece deshabilitado hasta que el cliente seleccione al menos un servicio, elija un profesional (o asignación automática) y marque un bloque horario continuo suficiente para cubrir la duración total acumulada (75 min). No se muestra ningún precio ni valor monetario en ningún paso.

### Estado 2: Intento de Reserva con Horario Solapado / Cruce de Agenda (Sad Path)
**Escenario cubierto:** Escenario 2: Intento de reserva en un horario con cruce o solapamiento (Sad Path)
**ID de Pantalla en Stitch:** `projects/12386224423209721294/screens/36c57b9bced7408d9bf9a7a461d028c6`
**Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  [LOGO] SPA PODOLÓGICO ÁMELY      [Interfaz de Fondo Atenuada por Overlay]        |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |  (!) ALERTA: CONFLICTO DE HORARIO EN TIEMPO REAL                          |   |
|   |---------------------------------------------------------------------------|   |
|   |  El bloque de tiempo seleccionado (10:30 - 11:45) se cruza con una cita   |   |
|   |  previamente reservada en la agenda del Lic. Carmen Silva.               |   |
|   |                                                                           |   |
|   |  Estado: [ BLOQUEO DE SEGURIDAD ACTIVO - RECHAZADO ]                      |   |
|   |                                                                           |   |
|   |  Horarios continuos libres alternativos para hoy (75 min):               |   |
|   |  [ Bloque 12:00 - 13:15 ]    [ Bloque 15:30 - 16:45 ]                    |   |
|   |                                                                           |   |
|   |  +-----------------------------------+   +----------------------------+   |   |
|   |  | ELEGIR HORARIO ALTERNATIVO        |   | CAMBIAR DE ESPECIALISTA    |   |   |
|   |  +-----------------------------------+   +----------------------------+   |   |
|   +---------------------------------------------------------------------------+   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```
**Nota de Interfaz:** Modal emergente con efecto backdrop-blur que bloquea la confirmación cuando el motor en tiempo real detecta un traslape de horarios con otra cita previa en la agenda del podólogo. Redirige al cliente a seleccionar un bloque libre continuo o cambiar de especialista.

### Estado 3: Verificación de Restricción Inquebrantable de No Precios
**Escenario cubierto:** Escenario 3: Verificación de Restricción Inquebrantable de No Precios
**ID de Pantalla en Stitch:** `projects/12386224423209721294/screens/cd3635f99991499a91cfec626e4ad361`
**Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  RESUMEN DE RESERVA DE CITA (RESTRICCIÓN RN-01 CUMPLIDA)                          |
|                                                                                   |
|  Servicios Seleccionados: Quiropodia Completa + Tratamiento Láser                 |
|  Duración Estimada Total: 75 minutos                                              |
|  Especialista Asignado: Lic. Carmen Silva                                         |
|  Fecha y Hora: 15/09/2026 | 09:00 - 10:15                                       |
|                                                                                   |
|  [ VALORES MONETARIOS / PRECIOS: OMISION ESTRICTA Y GARANTIZADA ]                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | [ CITA RESERVADA CON ÉXITO - NOTIFICACIÓN ENVIADA POR WHATSAPP ]            |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```
**Nota de Interfaz:** Cumplimiento estricto de la Regla de Negocio RN-01. El resumen de reserva muestra exclusivamente la duración en minutos, los nombres de los servicios y del especialista, omitiendo absolutamente cualquier símbolo de moneda ($/S/.), costo o tarifa.


## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - **Suma visible de duración en tiempo real:** Se incluye un indicador destacado de "Duración Total Acumulada" que se actualiza dinámicamente según los servicios marcados, permitiendo al cliente comprender de forma directa la amplitud del bloque de tiempo necesario.
  - **Prevención de errores y conflicto claro:** En caso de cruces de horarios, el sistema no solo notifica el bloqueo sino que presenta sugerencias inmediatas de slots contiguos sin solapamiento para reducir la fricción del usuario.
  - **Diseño sin fricción comercial:** Se eliminó cualquier etiqueta de precios, carrito o costo acumulado en concordancia con la regla RN-01.

- **Bloqueos o Consultas (Si aplican):**
  - **Identificación de cliente (Punto Abierto BA-01):** Se colocó un formulario con Nombre y WhatsApp/Teléfono en la UI. Pendiente confirmar por BA/Stakeholder si se implementará autenticación formal o código de reserva para consultas/anulaciones posteriores.


## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@PM: Los wireframes para la HU Reserva e Integración de Citas Podológicas en Tiempo Real están listos en D:\Paulo\Cursos\DMC\template-bmad\files\designer-ux\ux_01_motor_reservas.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
