# PLAN DE GESTIÓN Y BACKLOG DEL MVP - ÁMELY SPÁ PODOLÓGICO

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Construir un motor de reservas inteligente e integral que permita la selección multiservicio y la asignación de podólogos con cálculo dinámico de tiempos y bloqueo de agendas en tiempo real, respaldado por notificaciones automáticas inmediatas vía WhatsApp para eliminar los cruces de citas y optimizar la atención operativa.
- **Criterio de Éxito Rector:** Lograr una reducción al 0% de sobreposiciones de citas y errores en la estimación del tiempo acumulado en agendamientos multiservicio, garantizando un 100% de oportunidad en el envío de notificaciones de confirmación y cancelación por WhatsApp.


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor de Reservas Inteligente y Control de Disponibilidad
  - *Justificación de Prioridad:* Constituye el núcleo (Core) operativo del sistema. Sin la capacidad de seleccionar múltiples servicios, elegir al podólogo preferido, calcular automáticamente la duración acumulada y bloquear en tiempo real el bloque horario exacto, no es posible resolver el problema crítico de solapamiento de agendas y tiempos muertos.
  - *Trazabilidad:* Responde a la Sección 4 (Punto 2: "Motor de Reservas Inteligente y Control de Disponibilidad") y a los Criterios de Éxito de 0% sobreposiciones y 0% errores de estimación de tiempo.

- **[P2] Épica:** Notificaciones Automáticas e Inmediatas vía WhatsApp
  - *Justificación de Prioridad:* Representa la capa de comunicación y confirmación inmediata esencial para asegurar la puntualidad y la reducción de inasistencias. Se prioriza inmediatamente después de P1 porque depende de los eventos disparados por la creación y cancelación de reservas.
  - *Trazabilidad:* Responde a la Sección 4 (Punto 3: "Notificaciones Inmediatas vía WhatsApp") y a la Restricción de canal obligatorio por WhatsApp.

- **[P3] Épica:** Dashboard de Gestión para Podólogos y Autogestión de Citas para Clientes
  - *Justificación de Prioridad:* Ofrece las interfaces de control para los actores principales: el panel diario/semanal para que los podólogos gestionen su jornada y la funcionalidad de cancelación autónoma para los clientes.
  - *Trazabilidad:* Responde a la Sección 4 (Punto 4: "Panel de Gestión para Profesionales y Autogestión del Cliente").

- **[P4] Épica:** Vitrina Digital e Identidad del Spá
  - *Justificación de Prioridad:* Proporciona la cara pública informativa de la plataforma (presentación del equipo de podólogos y catálogo de servicios con tiempos estimados sin precios). Complementa la experiencia de reserva previa a la selección.
  - *Trazabilidad:* Responde a la Sección 4 (Punto 1: "Vitrina Digital e Identidad del Spá") y a la Restricción estricta de ocultación de precios.


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:**
  - *Dependencia de Integración WhatsApp:* La obligatoriedad del uso exclusivo de WhatsApp requiere definir la API/Proveedor técnico (ej. WhatsApp Business API) para asegurar la entrega oportuna de notificaciones.
  - *Definición de Horarios y Ausencias:* Supuesto de que la disponibilidad de los podólogos está estructurada; sin embargo, no se define el mecanismo de gestión para turnos, días laborables o descansos en el sistema.

- **Ambigüedades de Negocio:**
  - *Políticas de Cancelación:* Ausencia de reglas sobre el tiempo mínimo de anticipación requerido para cancelar una cita.
  - *Verificación de Datos del Cliente:* Falta precisar qué datos personales (Nombre, WhatsApp, Correo, DNI) son obligatorios y si se requiere validación/verificación previa a confirmar la reserva.
  - *Reprogramación de Citas:* No se explicita si se permite modificar fecha/hora o si el alcance del MVP se limita únicamente a cancelar y volver a agendar.
  - *Restricción de Precios:* Recordatorio estricto de que en ninguna pantalla ni notificación pública se deben exponer precios.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor de Reservas Inteligente y Control de Disponibilidad. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: Definir los datos personales obligatorios solicitados al cliente y verificar cómo se valida la disponibilidad en tiempo real sin exponer precios ni permitir cruces de agenda. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
