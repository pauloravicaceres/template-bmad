## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Digitalizar y automatizar el flujo principal de reserva inteligente de citas y validación de disponibilidad en tiempo real para clientes y profesionales podólogos del Spa Ámely, integrando notificaciones automáticas por WhatsApp y eliminando por completo los cruces de horarios, bajo la regla estricta de no mostrar precios.
- **Criterio de Éxito Rector:** Lograr un 0% de cruces o solapamientos de citas asignadas a un mismo profesional podólogo y garantizar un 100% de notificaciones instantáneas de confirmación y anulación entregadas vía WhatsApp.


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor Inteligente de Reservas y Disponibilidad en Tiempo Real
  - *Justificación de Prioridad:* Representa la funcionalidad núcleo (Core) del MVP. Sin la capacidad de seleccionar uno o varios servicios, calcular la duración acumulada, validar disponibilidad en tiempo real y bloquear el bloque horario sin solapamientos, el producto no puede resolver el problema de cruces ni cumplir su objetivo principal.
  - *Trazabilidad:* Responde directamente a la sección "3. Objetivo" (eliminar cruces de horarios) y a la sección "4. Alcance Inicial - Motor Inteligente de Reservas y Disponibilidad".

- **[P2] Épica:** Sistema de Notificaciones Automáticas por WhatsApp
  - *Justificación de Prioridad:* Complementa de forma directa el flujo de reserva y anulación, enviando confirmaciones y alertas inmediatas al cliente y al profesional podólogo para asegurar la comunicación en tiempo real.
  - *Trazabilidad:* Responde a la sección "3. Objetivo" (notificación en tiempo real por WhatsApp) y "4. Alcance Inicial - Sistema de Notificaciones por WhatsApp".

- **[P3] Épica:** Catálogo de Servicios y Vitrina del Equipo Profesional
  - *Justificación de Prioridad:* Proporciona la interfaz de entrada donde los clientes exploran el personal podólogo especializado y seleccionan servicios (visualizando únicamente descripción y duración estimada, sin precios) para iniciar el agendamiento.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Vitrina del Equipo Profesional" y "Catálogo de Servicios (Sin Precios)".

- **[P4] Épica:** Módulo de Anulación de Citas por el Cliente
  - *Justificación de Prioridad:* Permite a los clientes cancelar citas previas de manera autónoma, liberando automáticamente el bloque de tiempo en la agenda del profesional y disparando la notificación correspondiente por WhatsApp.
  - *Trazabilidad:* Responde a la sección "2. Usuarios - Clientes" (anular citas autónomamente) y "4. Alcance Inicial - Opción de anulación de citas previas".

- **[P5] Épica:** Panel de Gestión de Citas para Profesionales Podólogos
  - *Justificación de Prioridad:* Proporciona a los especialistas un módulo privado para consultar su agenda diaria en tiempo real y hacer seguimiento a sus atenciones durante la jornada laboral.
  - *Trazabilidad:* Responde a la sección "2. Usuarios - Profesionales Podólogos" y "4. Alcance Inicial - Panel de Gestión de Citas para Profesionales".


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:** 
  - Dependencia técnica crítica del canal externo de WhatsApp para la entrega de confirmaciones y notificaciones de anulación; cualquier falla en dicha integración afectará directamente el criterio de éxito del 100% de entregabilidad.
  - La precisión de la disponibilidad depende de la exactitud del supuesto de que la suma de duraciones promedio de los servicios seleccionados refleja fielmente la duración real de la atención.
- **Ambigüedades de Negocio:**
  - *Mecanismo de Identificación/Autenticación:* El PRD no especifica cómo los clientes consultan o anulan sus citas (ej. número telefónico, código único de reserva o correo).
  - *Políticas de Cancelación y Anticipación:* Ausencia de reglas de negocio sobre el tiempo mínimo de anticipación requerido para agendar o anular una cita.
  - *Horarios y Gestión de Turnos:* Falta definir los horarios oficiales del spa y la gestión de descansos o turnos de cada podólogo.
  - *Regla Inquebrantable de Negocio:* Estricta prohibición de mostrar precios en el catálogo, reserva o notificaciones.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

`@BA: El análisis estratégico está completo en el archivo mvp_amely_spa.md. Tu primera asignación es leer ese documento y desglosar la Épica **[P1]**: Motor Inteligente de Reservas y Disponibilidad en Tiempo Real. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: Se debe respetar estrictamente la regla inquebrantable de no mostrar precios en ningún punto del flujo y considerar que la forma de identificación del cliente para consultar/gestionar citas no está definida en el PRD. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.`
