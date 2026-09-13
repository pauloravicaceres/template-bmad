# ESPECIFICACIÓN DE DISEÑO UX DE INTERFAZ

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Agendamiento de cita podológica y reserva de horario en tiempo real
- **Enfoque de Usabilidad:** Se diseñó un flujo de reserva asistido por acumulación dinámica de tiempo, donde la selección de múltiples servicios calcula automáticamente la duración total requerida y filtra en tiempo real los bloques continuos disponibles, previniendo solapamientos en la agenda del especialista.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Selección de Servicios y Horario Disponible (Happy Path)

**Escenario cubierto:** Escenario 1: Agendamiento exitoso de atención podológica sin solapamientos (Happy Path)

**Artefacto Visual (Stitch):**
- **Project ID:** `16279583536780402562`
- **Screen ID:** `f21408eb99bd4ff085689cb094846c13`
- **Link de recurso:** `projects/16279583536780402562/screens/f21408eb99bd4ff085689cb094846c13`

**Nota de Interfaz:** 
El panel lateral acumula dinámicamente el tiempo de los servicios marcados (ej. Pedicura Médica 45m + Tratamiento Uñero 30m = 75 min). La parrilla de horarios únicamente resalta como seleccionables los bloques de tiempo continuos que cumplen con la duración total acumulada. El botón de acción "Confirmar Agendamiento" se habilita únicamente cuando el cliente completa la selección de servicios, especialista, fecha y un bloque disponible.

### Estado 2: Intento de Selección en Horario No Disponible / Solapado (Sad Path)

**Escenario cubierto:** Escenario 2: Intento de reserva en horario no disponible o solapado (Sad Path)

**Artefacto Visual (Stitch):**
- **Project ID:** `16279583536780402562`
- **Screen ID:** `3a5d0b4554fd4ae29dfd2178cbd67e43`
- **Link de recurso:** `projects/16279583536780402562/screens/3a5d0b4554fd4ae29dfd2178cbd67e43`

**Nota de Interfaz:** 
Si el usuario intenta hacer clic sobre un bloque reservado o solapado (ej. 05:00 PM - 06:15 PM), el sistema bloquea visualmente la interacción deshabilitando el slot (borde rojizo sutil / estado deshabilitado) y despliega un Toast / Banner de Alerta en pantalla con el mensaje: *"El bloque seleccionado ya ha sido reservado por otro cliente en tiempo real o no cuenta con el tiempo continuo necesario (75 min). Por favor selecciona un bloque resaltado en verde."* Además, el botón "Confirmar Agendamiento" permanece inhabilitado (`disabled`) hasta que se seleccione una opción válida.

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:** 
  - *Visibilidad del Estado del Sistema (Nielsen #1):* Cálculo visible en tiempo real del tiempo acumulado (75 min) y subtotal monetario.
  - *Prevención de Errores (Nielsen #5):* Deshabilitación visual e interactiva de horarios solapados y falta de duración continua previa a la confirmación.
  - *Consistencia y Estándares (Nielsen #4):* Sistema de diseño "Sanitas & Serenity" con paleta clínica relajante (Teal `#0D9488`, Menta `#F0FDFA`, Alerta Rosa `#FFF1F2`).
- **Bloqueos o Consultas (Si aplican):** 
  - *Mecanismo de Autenticación de Cliente:* Confirmar con el BA/Arquitecto si en la pantalla siguiente al agendamiento se requerirá ingreso de DNI/Teléfono o código OTP para asociar la cita al registro del paciente.

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@ARQ: Los wireframes funcionales para la Historia de Usuario Agendamiento de cita podológica y reserva de horario en tiempo real están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_01_agendamiento.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
