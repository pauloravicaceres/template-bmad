## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Construir y asegurar en primer lugar el motor inteligente de reservas con validación en tiempo real y bloqueo horario acumulativo por servicios seleccionados, eliminando por completo los cruces de agenda de los podólogos y automatizando las notificaciones de confirmación y anulación vía WhatsApp.
- **Criterio de Éxito Rector:** Lograr 0% de cruces o solapamientos en las citas agendadas por profesional podólogo y 100% de efectividad en el envío instantáneo de notificaciones vía WhatsApp para reservas y anulaciones.


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor Inteligente de Reservas y Gestión de Disponibilidad
  - *Justificación de Prioridad:* Es el corazón del negocio y el flujo crítico del MVP. Sin el cálculo acumulativo del tiempo total de atención y la validación en tiempo real de disponibilidad por profesional, se mantendrían los cruces de horario.
  - *Trazabilidad:* Responde a la Sección 4.2 del Product Brief ("Motor Inteligente de Reservas y Gestión de Disponibilidad") y a los Objetivos de eliminar solapamiento de citas.

- **[P2] Épica:** Gestión de Citas y Anulaciones para Clientes y Podólogos
  - *Justificación de Prioridad:* Complementa la reserva permitiendo al cliente cancelar su cita de forma autónoma mediante código/enlace y liberando la agenda al instante, mientras provee al podólogo un panel diario de seguimiento.
  - *Trazabilidad:* Responde a la Sección 4.4 del Product Brief ("Gestión de Citas y Cancelaciones") y a los Criterios de Éxito de liberación inmediata de agenda.

- **[P3] Épica:** Sistema de Notificaciones Automatizadas por WhatsApp
  - *Justificación de Prioridad:* Asegura la confirmación inmediata y la comunicación fluida con el cliente y el podólogo ante nuevas reservas o cancelaciones.
  - *Trazabilidad:* Responde a la Sección 4.3 del Product Brief ("Sistema de Notificaciones Automatizadas por WhatsApp") y Restricción de canal único obligatorio.

- **[P4] Épica:** Módulo de Vitrina Digital y Catálogo de Servicios Podológicos
  - *Justificación de Prioridad:* Otorga la interfaz pública visual para la selección de servicios y profesionales antes de iniciar el proceso de agendamiento.
  - *Trazabilidad:* Responde a la Sección 4.1 del Product Brief ("Módulo de Vitrina Digital y Equipo") manteniendo la restricción de precios ocultos al público.


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:**
  - Dependencia de un proveedor o API externa de WhatsApp Business para garantizar el envío instantáneo del 100% de notificaciones. Si no se define el proveedor o plantilla, no se podrá validar el flujo completo de notificaciones en tiempo real.
  - Ausencia de un mecanismo definido para configurar los turnos, pausas y días festivos de cada podólogo en el sistema.

- **Ambigüedades de Negocio:**
  - **Captura de datos obligatorios del cliente:** No se especifican en el Product Brief los campos exactos requeridos al reservar (ej. nombre completo, teléfono WhatsApp, correo, notas médicas).
  - **Políticas de anulación:** No se especifica un margen mínimo de tiempo (ej. 2 horas antes de la cita) para permitir anulaciones por código/enlace sin penalización.
  - **Reglas de administración del spa:** No se definen las pantallas ni permisos para que la administración cree o modifique servicios y podólogos en el MVP.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely_spa.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor Inteligente de Reservas y Gestión de Disponibilidad. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: Definición de los datos personales obligatorios que se deben capturar del cliente en la reserva y la gestión de los turnos laborales y pausas del podólogo para el bloqueo del bloque horario. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
