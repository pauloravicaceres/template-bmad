# PLAN DE GESTIÓN Y MVP: Ámely - Spá Podológico

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Construir prioritariamente el flujo automatizado de reservas inteligentes y control de disponibilidad sin cruces de horario, garantizando que los clientes puedan agendar servicios simples o combinados con su podólogo de preferencia y que el sistema calcule el tiempo total estimado de atención en tiempo real.
- **Criterio de Éxito Rector:** Registrar cero superposiciones o cruces de horarios en las agendas de los podólogos tras la entrada en funcionamiento y asegurar la entrega inmediata de avisos de confirmación y cancelación vía WhatsApp.

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor de Reservas Inteligente y Control de Disponibilidad
  - *Justificación de Prioridad:* Es la funcionalidad core indispensable del sistema; sin la selección de servicios/podólogos, el cálculo acumulativo de tiempo y el bloqueo de agenda en tiempo real, no se resuelve el problema central de cruce de horarios.
  - *Trazabilidad:* Responde directamente a la sección "Motor de Reservas Inteligente y Control de Disponibilidad" del Alcance Inicial y al Objetivo principal del Product Brief.

- **[P2] Épica:** Sistema de Notificaciones Instantáneas y Anulación por WhatsApp
  - *Justificación de Prioridad:* Es esencial para garantizar la confirmación de las reservas y permitir al cliente anular citas liberando inmediatamente la agenda del podólogo.
  - *Trazabilidad:* Responde a la sección "Sistema de Notificaciones Instantáneas por WhatsApp" del Alcance Inicial y a la comunicación en tiempo real requerida por el negocio.

- **[P3] Épica:** Panel de Gestión de Citas para Profesionales Podólogos
  - *Justificación de Prioridad:* Otorga visibilidad operativa al equipo de podólogos para el seguimiento diario de su agenda y estados de atención en tiempo real.
  - *Trazabilidad:* Responde a la sección "Panel de Gestión de Citas para Profesionales" del Alcance Inicial y a la optimización del tiempo del equipo.

- **[P4] Épica:** Vitrina Digital de Servicios y Equipo Profesional
  - *Justificación de Prioridad:* Proporciona la interfaz de presentación institucional, catálogo de servicios y perfiles podológicos para contextualizar la navegación del cliente antes del agendamiento.
  - *Trazabilidad:* Responde a la sección "Vitrina Digital y Equipo Profesional" del Alcance Inicial, respetando la Restricción Comercial de no mostrar precios.

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:**
  - Dependencia técnica de la API/servicio de WhatsApp para el envío de notificaciones automáticas y enlaces de anulación.
  - Ambigüedad sobre el modelo de acceso del cliente: no se especifica si requerirá cuenta de usuario o si la gestión/anulación se realizará mediante token o enlace único vía WhatsApp.

- **Ambigüedades de Negocio:**
  - **Horarios y turnos:** Falta definir el horario de atención del spá y la gestión de descansos/turnos específicos de cada podólogo.
  - **Ventanas de anticipación:** No se establecieron los tiempos mínimos y máximos requeridos para agendar o anular una cita.
  - **Restricción Comercial de Precios:** Debe asegurarse que ningún catálogo o vista exponga precios de servicios.
  - **Plantillas de mensaje:** Falta definir la estructura y contenido exacto de las notificaciones de WhatsApp.

## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely_spa.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor de Reservas Inteligente y Control de Disponibilidad. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: No se especifica si la gestión/anulación requiere cuenta de usuario o enlace único vía WhatsApp, ni las ventanas de anticipación o turnos específicos de los podólogos. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
