# PLAN DE GESTIÓN DE PRODUCTO Y BACKLOG MVP - ÁMELY SPÁ PODOLÓGICO

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** El foco prioritario de este MVP es construir el flujo principal de reserva multimodular y validación de disponibilidad en tiempo real, garantizando la eliminación absoluta de cruces de agenda entre podólogos y el cálculo preciso de duraciones sumadas de atención para Ámely - Spá Podológico.
- **Criterio de Éxito Rector:** Lograr 0% de solapamiento de citas registradas en los horarios de atención de los podólogos y reducir la tasa de inasistencias (no-shows) mediante un flujo automatizado de confirmaciones por WhatsApp.


## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor Inteligente de Reservas y Disponibilidad
  - *Justificación de Prioridad:* Es la funcionalidad núcleo (Core) transaccional. Sin la lógica de validación de agenda en tiempo real, suma de duraciones y bloqueo de bloques horarios, no es posible resolver el problema principal del negocio ni habilitar la autogestión de citas.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Punto 2" y a las restricciones de integridad de agenda.
- **[P2] Épica:** Vitrina Digital de Podólogos y Servicios
  - *Justificación de Prioridad:* Es el prerrequisito del cliente para visualizar el catálogo de servicios podológicos (con duraciones y precios) y la plantilla de profesionales antes de proceder con el agendamiento.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Punto 1".
- **[P3] Épica:** Notificaciones Automatizadas por WhatsApp
  - *Justificación de Prioridad:* Mecanismo clave para mitigar las inasistencias y notificar inmediatamente al podólogo ante cualquier modificación o cancelación en la agenda.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Punto 3" y a la restricción del canal mandatorio de WhatsApp.
- **[P4] Épica:** Panel de Gestión para Podólogos
  - *Justificación de Prioridad:* Interfaz operativa interna que habilita a los podólogos la visualización y el seguimiento en tiempo real del estado de sus atenciones agendadas.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Punto 4".
- **[P5] Épica:** Módulo de Auto-Gestión y Cancelación para Clientes
  - *Justificación de Prioridad:* Permite a los clientes anular citas oportunamente, liberando espacios en la agenda para maximizar la ocupación del spá.
  - *Trazabilidad:* Responde a la sección "4. Alcance Inicial - Punto 5".


## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:**
  - Dependencia directa de un proveedor/API de WhatsApp (ej. Twilio o Meta Business API); si la integración o las plantillas de notificaciones no están configuradas, se bloquea el envío automático de confirmaciones/anulaciones.
  - Asunción de precisión en las duraciones estimadas por tratamiento podológico; variaciones significativas en la práctica real podrían descuadrar el bloque agendado.
- **Ambigüedades de Negocio:**
  - **Política de Cancelación:** No existe especificación sobre el tiempo límite mínimo (ej. 2h, 12h o 24h previas) para permitir la anulación sin penalidad por parte del cliente.
  - **Mecanismo de Autenticación del Cliente:** El PRD no aclara si el cliente creará un usuario con contraseña o si utilizará un token/código de reserva junto a su número telefónico.
  - **Modelo de Pago:** Falta definir si el cobro es presencial en el spá o si se requerirá un anticipo/seña digital para reservar.
  - **Estados de Atención en Panel:** No se definen los estados exactos (ej. *Pendiente*, *En Atención*, *Completado*, *No Asistió*) ni si se registrarán notas clínicas/observaciones.


## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_spa_amely.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor Inteligente de Reservas y Disponibilidad. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: El mecanismo exacto de autenticación del cliente (por contraseña vs. código/teléfono) y las reglas/límites de tiempo para la cancelación no están definidos en el Product Brief. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
