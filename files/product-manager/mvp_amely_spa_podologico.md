# PLAN DE GESTIÓN Y MVP: Ámely - Spá Podológico

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** El equipo debe concentrarse primordialmente en la construcción del motor de reservas inteligente y el flujo de bloqueo de horarios en tiempo real. La prioridad operativa es erradicar el traslape de citas en las agendas de los podólogos y automatizar la confirmación/anulación de reservas mediante notificaciones inmediatas por WhatsApp.
- **Criterio de Éxito Rector:** Reducción total de cruces de agenda (0 incidentes reportados por duplicidad o sobreposición de reservas en la agenda de un profesional).


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor de Reservas Inteligente y Validación de Disponibilidad
  - *Justificación de Prioridad:* Representa la funcionalidad núcleo (Core) del producto. Sin la capacidad de seleccionar podólogo, acumular duraciones estimadas de servicios y bloquear horarios en tiempo real sin cruces, el sistema no resuelve el problema operativo central del spá.
  - *Trazabilidad:* Responde a las secciones "3. Objetivo" (eliminar cruces de horarios) y "4. Alcance Inicial - Motor de Reservas Inteligente y Validación de Disponibilidad" del Product Brief.

- **[P2] Épica:** Sistema de Notificaciones Automáticas e Inmediatas por WhatsApp
  - *Justificación de Prioridad:* Depende directamente de las acciones del motor de reservas. Garantiza la confirmación síncrona al cliente y podólogo tras reservar, así como la alerta inmediata de cancelación para liberar disponibilidad.
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Sistema de Notificaciones por WhatsApp" y a los supuestos/criterios de éxito de notificaciones informativas por WhatsApp.

- **[P3] Épica:** Panel de Gestión para Podólogos y Autogestión de Cancelaciones por Clientes
  - *Justificación de Prioridad:* Otorga al podólogo visibilidad en tiempo real de su jornada laboral y permite al cliente anular autónomamente reservas respetando las restricciones operativas.
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Panel de Gestión de Citas para Profesionales" y a la autogestión de citas del cliente.

- **[P4] Épica:** Vitrina Digital de Profesionales y Servicios
  - *Justificación de Prioridad:* Constituye el punto de entrada informativo donde los clientes exploran los podólogos y el catálogo de servicios con tiempos promedios (respetando la restricción de no exhibir precios).
  - *Trazabilidad:* Responde a "4. Alcance Inicial - Vitrina de Profesionales y Servicios" y la restricción de "Ocultamiento Estratégico de Precios".


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:**
  - Integración y disponibilidad de la infraestructura API de WhatsApp para notificaciones automáticas inmediatas; una falla en este proveedor externo impediría la confirmación inmediata.
  - La validez de calcular el tiempo total de la cita sumando linealmente las duraciones promedio de múltiples servicios sin considerar tiempos muertos o preparación intermedia.
- **Ambigüedades de Negocio:**
  - *Datos obligatorios de reserva:* No se especifican los campos de identificación personal mínimos (ej. nombre completo, WhatsApp, correo) requeridos para efectuar una cita.
  - *Límite de tiempo para cancelaciones:* Se desconoce la ventana límite (ej. cuantas horas antes) permitida para la anulación autónoma por parte del cliente.
  - *Gestión de horarios y turnos de podólogos:* Falta definir la administración de jornadas laborales, descansos y ausencias.
  - *Reagendamiento de citas:* No se precisa si el cliente puede reprogramar una cita directamente o si debe anular y crear una nueva.
  - *Rol de Administrador General:* No se ha definido un módulo administrativo central para dar de alta/baja servicios o personal.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely_spa_podologico.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor de Reservas Inteligente y Validación de Disponibilidad. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: Definir los datos personales mínimos requeridos para la reserva del cliente y establecer las reglas exactas para la validación síncrona de disponibilidad y cálculo de tiempos sin mostrar precios. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
