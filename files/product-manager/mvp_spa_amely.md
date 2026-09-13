## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Construir el motor inteligente de reservas y agendamiento sin solapamientos, integrado a la vitrina digital de servicios y podólogos, para eliminar la gestión manual de citas y garantizar una asignación fluida de horarios.
- **Criterio de Éxito Rector:** Lograr un 0% de solapamiento/cruces de citas en los horarios de los podólogos y reducir la tasa de inasistencias (no-shows) mediante notificaciones automáticas por WhatsApp y autogestión de cancelaciones.


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

Organiza el alcance en grandes bloques de valor, ordenados por prioridad estricta de ejecución:

- **[P1] Épica:** Motor Inteligente de Reservas y Disponibilidad
  - *Justificación de Prioridad:* Constituye el núcleo operativo del producto. Sin la selección multimodular de servicios, el cálculo automático de duraciones y la validación en tiempo real para evitar solapamientos, el producto no cumple su propósito principal de resolver los cruces de agenda.
  - *Trazabilidad:* Responde a la Sección 3 (Objetivos) y a la Sección 4.2 (Alcance Inicial: Motor Inteligente de Reservas y Disponibilidad del Product Brief).
- **[P2] Épica:** Vitrina Digital de Podólogos y Servicios
  - *Justificación de Prioridad:* Permite a los clientes visualizar el catálogo de tratamientos con sus duraciones/precios y seleccionar al profesional de su preferencia, proporcionando los insumos necesarios para iniciar el flujo de reserva (P1).
  - *Trazabilidad:* Responde a la Sección 4.1 (Alcance Inicial: Vitrina Digital de Podólogos y Servicios del Product Brief).
- **[P3] Épica:** Notificaciones Automatizadas por WhatsApp
  - *Justificación de Prioridad:* Requisito mandatorio para enviar confirmaciones inmediatas tras reservar y notificar cancelaciones, reduciendo la tasa de inasistencias e informando al podólogo oportunamente.
  - *Trazabilidad:* Responde a la Sección 4.3 (Alcance Inicial: Notificaciones Automatizadas por WhatsApp) y Sección 5 (Restricciones).
- **[P4] Épica:** Panel de Gestión para Podólogos
  - *Justificación de Prioridad:* Proporciona al equipo médico una interfaz privada para monitorear y actualizar en tiempo real el estado de sus citas programadas, dependiendo directamente de las reservas generadas en P1.
  - *Trazabilidad:* Responde a la Sección 4.4 (Alcance Inicial: Panel de Gestión para Podólogos) y Sección 2 (Usuarios: Podólogos).
- **[P5] Épica:** Módulo de Auto-Gestión y Cancelación para Clientes
  - *Justificación de Prioridad:* Facilita la anulación oportuna de citas por parte del cliente, permitiendo liberar espacios en la agenda y disparar notificaciones de cancelación (P3).
  - *Trazabilidad:* Responde a la Sección 4.5 (Alcance Inicial: Módulo de Auto-Gestión y Cancelación para Clientes).


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:** 
  - Dependencia técnica de la integración con un proveedor de API empresarial de WhatsApp (ej. Twilio o Meta Business API) para garantizar la transmisión efectiva de confirmaciones y alertas de cancelación.
  - Margen de error en las duraciones estimadas por servicio, lo que podría desajustar la acumulación de tiempos en reservas multimodulares y generar retrasos presenciales.
- **Ambigüedades de Negocio:** 
  - Política de Cancelación: No se ha definido un tiempo límite mínimo de anticipación (ej. 2, 12 o 24 horas antes) para permitir la anulación en línea por parte del cliente.
  - Autenticación del Cliente: Indefinición sobre si se requiere registro/inicio de sesión o si se agendará/cancelará mediante un identificador único (número telefónico o código de reserva).
  - Modelo de Pago: Incertidumbre sobre si la reserva exige pago previo/seña en línea o si el cobro es 100% presencial.
  - Estados del Panel del Podólogo: Falta precisar el listado oficial de estados de la atención (ej. Pendiente, En Atención, Completado, No Asistió) y si se registrarán observaciones clínicas.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo. Tu primera asignación es desglosar la Épica de Prioridad 1: Motor Inteligente de Reservas y Disponibilidad. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: Identificar el mecanismo exacto de autenticación/identificación del cliente y no asumir políticas de pago o reglas de cancelación no delimitadas. Procederé a revisar tu entregable una vez pase por QA Documental.
