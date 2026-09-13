# PLAN DE GESTIÓN Y BACKLOG MVP - ÁMELY SPÁ PODOLÓGICO

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Automatizar integralmente la reserva e integración de agendas en tiempo real para erradicar solapamientos de citas y eliminar imprecisiones en el cálculo de duración de atenciones combinadas, ofreciendo una experiencia web adaptable y ligera.
- **Criterio de Éxito Rector:** Reducción al 0% de solapamientos o citas duplicadas en las agendas de los podólogos y 100% de efectividad en la entrega inmediata de notificaciones vía WhatsApp.

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor de Reservas e Integración de Agenda en Tiempo Real
  - *Justificación de Prioridad:* Constituye el núcleo operativo y la propuesta de valor central del MVP. Sin la capacidad de calcular dinámicamente el tiempo de servicios combinados y validar la disponibilidad sin solapamientos en tiempo real, el producto no puede resolver el problema de ineficiencia operativa.
  - *Trazabilidad:* Responde a la sección "Objetivo" (Automatizar reservas e integrar agendas) y al punto 2 de "Alcance Inicial" (Motor de Reservas e Integración de Agenda).

- **[P2] Épica:** Catálogo Digital de Servicios y Especialistas
  - *Justificación de Prioridad:* Es el componente visual indispensable para que el cliente consulte la oferta podológica y seleccione especialistas/servicios antes de iniciar el flujo de reserva.
  - *Trazabilidad:* Responde al punto 1 de "Alcance Inicial" (Catálogo Digital de Servicios y Especialistas) y la restricción de ocultamiento de precios.

- **[P3] Épica:** Notificaciones Automáticas por WhatsApp
  - *Justificación de Prioridad:* Garantiza la confirmación e información inmediata al cliente y especialista tras agendar o cancelar una cita. Depende directamente de la emisión de eventos desde el motor de reservas y anulación.
  - *Trazabilidad:* Responde al punto 3 de "Alcance Inicial" (Notificaciones por WhatsApp) y a los Supuestos/Criterios de éxito de comunicación.

- **[P4] Épica:** Módulo de Anulación de Citas por el Cliente
  - *Justificación de Prioridad:* Permite la autogestión del cliente para liberar slots de agenda en caso de no poder asistir. Requiere la existencia previa de citas agendadas por el motor de reservas.
  - *Trazabilidad:* Responde al punto 4 de "Alcance Inicial" (Módulo de Anulación de Citas).

- **[P5] Épica:** Panel de Gestión de Atenciones para Podólogos
  - *Justificación de Prioridad:* Proporciona una interfaz dedicada para que cada podólogo revise su agenda individual y dé seguimiento a sus atenciones programadas durante la jornada laboral.
  - *Trazabilidad:* Responde al punto 5 de "Alcance Inicial" (Panel de Gestión de Atenciones para Podólogos).

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:** 
  - Dependencia externa de la API/Proveedor de WhatsApp para el envío de notificaciones automáticas (si no hay proveedor definido o credenciales, se bloquea la confirmación al usuario).
  - Precisión de los tiempos promedios definidos para los servicios podológicos combinados (si no son exactos, pueden generar descalces en la atención física).
- **Ambigüedades de Negocio:**
  - Mecanismo de autenticación e identificación del cliente al agendar o anular citas (ej. número celular, DNI, correo o código por WhatsApp).
  - Políticas y restricciones de tiempo previo para la anulación de citas por parte del cliente (ej. ventana mínima de horas antes de la cita).
  - Definición sobre si se permitirá reprogramación directa o solo anulación y nueva reserva.

## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely_spa.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor de Reservas e Integración de Agenda en Tiempo Real. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: El mecanismo exacto de identificación y autenticación del cliente al agendar la cita no está definido en el PRD. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
