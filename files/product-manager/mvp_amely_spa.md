# PLAN DE GESTIÓN Y ESTRATEGIA MVP - ÁMELY SPÁ PODOLÓGICO

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** El foco prioritario se centra en construir el motor de agendamiento y reserva de citas en tiempo real, garantizando la eliminación total de solapamientos de horarios en las agendas de los podólogos y una experiencia fluida mobile-first para el cliente.
- **Criterio de Éxito Rector:** Cero (0%) cruces de horario en la disponibilidad de los podólogos y entrega inmediata de notificaciones de confirmación/anulación por WhatsApp.


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor de Reservas e Integración de Agenda en Tiempo Real
  - *Justificación de Prioridad:* Es la funcionalidad núcleo (Core) del negocio. Sin la gestión de disponibilidad y reserva continua de horarios sin solapamientos, el producto no resuelve el problema principal de ineficiencia operativa.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Punto 2: Motor de Reservas y Agenda Inteligente" y "3. Objetivo (Outcome) - Cero cruces de agenda".

- **[P2] Épica:** Catálogo Digital de Servicios y Especialistas
  - *Justificación de Prioridad:* Es requerida como paso previo/complementario en el flujo de usuario para seleccionar profesional y servicios antes o durante la reserva, pero depende conceptualmente del motor de tiempos.
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Punto 1: Vitrina Digital de Personal y Servicios" y la restricción de ocultamiento de precios.

- **[P3] Épica:** Notificaciones Automáticas por WhatsApp
  - *Justificación de Prioridad:* Garantiza la confirmación inmediata y reduce la gestión manual, pero actúa como un canal de salida integrado a las acciones de reserva/anulación.
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Punto 4: Sistema de Notificaciones vía WhatsApp" y "5. Restricciones - Canal Obligatorio".

- **[P4] Épica:** Módulo de Anulación de Citas por el Cliente
  - *Justificación de Prioridad:* Oculta o libera disponibilidad en la agenda cuando un cliente no puede asistir, completando el ciclo de vida de la reserva.
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Punto 3: Gestión de Anulación de Reservas por Clientes".

- **[P5] Épica:** Panel de Gestión de Atenciones (Portal Profesional)
  - *Justificación de Prioridad:* Permite a los podólogos visualizar sus citas agendadas y dar seguimiento a su estado en el spa.
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Punto 5: Panel de Gestión de Atenciones (Portal Profesional)".


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:** La integración exclusiva con WhatsApp depende de contar con una API/Proveedor operativo (Twilio, Meta WhatsApp Business API). Si no se define el proveedor o credenciales, se bloqueará el canal de notificación.
- **Ambigüedades de Negocio:**
  - Identificación del cliente: No se especifica si requiere registro/login o solo datos básicos (Nombre, Teléfono, DNI).
  - Tiempos de anulación: No hay política explícita sobre el límite de tiempo previo para cancelar una cita.
  - Margen entre citas: No se especifica si se debe calcular tiempo de desinfección/limpieza entre atenciones consecutivas.
  - Administración de catálogo/podólogos: No se detalla si existirá un módulo administrativo para alta/baja de personal y servicios en el MVP.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely_spa.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor de Reservas e Integración de Agenda en Tiempo Real. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: El mecanismo exacto de identificación y autenticación del cliente al agendar la cita no está definido en el PRD. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
