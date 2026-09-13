# PLAN DE GESTIÓN Y ESTRATEGIA DEL MVP: Ámely - Spá Podológico

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** El foco principal del sprint es construir e integrar el flujo transaccional autónomo de reservas podológicas y notificaciones instantáneas, permitiendo al cliente seleccionar servicios y agendar citas en tiempo real sin cruces de agenda, mientras se automatizan las confirmaciones y alertas al personal mediante WhatsApp.
- **Criterio de Éxito Rector:** Alcanzar un 0% de solapamientos/cruces involuntarios en las agendas de los podólogos y la emisión inmediata (< 1 minuto) de notificaciones por WhatsApp tras cada reserva o cancelación.

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

- **[P1] Épica:** Motor Inteligente de Reservas y Agenda Dinámica
  - *Justificación de Prioridad:* Es el núcleo operativo y funcional del producto. Sin la capacidad de calcular la duración acumulada de servicios multilista, validar disponibilidad en tiempo real y bloquear intervalos continuos, el sistema no resuelve el problema de los cruces de agenda ni la ineficiencia manual.
  - *Trazabilidad:* Responde a los Objetivos 1 y 2, y al Punto 2 del Alcance Inicial del Product Brief.

- **[P2] Épica:** Sistema Integrado de Notificaciones vía WhatsApp
  - *Justificación de Prioridad:* Es la herramienta crítica de comunicación en tiempo real que mitiga los no-shows y asegura la confirmación inmediata tanto para el cliente como para el podólogo tras un agendamiento o anulación.
  - *Trazabilidad:* Responde al Objetivo 3 y al Punto 3 del Alcance Inicial del Product Brief.

- **[P3] Épica:** Panel de Gestión de Citas (Portal del Profesional)
  - *Justificación de Prioridad:* Permite a los podólogos visualizar su agenda diaria actualizada, revisar el historial de clientes y gestionar el estado de las citas (confirmada, atendida, cancelada).
  - *Trazabilidad:* Responde al Punto 4 del Alcance Inicial del Product Brief.

- **[P4] Épica:** Módulo de Gestión / Cancelación de Citas por el Cliente
  - *Justificación de Prioridad:* Permite al cliente solicitar la anulación autónoma de su cita agendada, liberando de forma inmediata el bloque de tiempo en la agenda del podólogo y disparando alertas por WhatsApp.
  - *Trazabilidad:* Responde al Punto 5 del Alcance Inicial del Product Brief.

- **[P5] Épica:** Vitrina Digital Institucional y Catálogo de Servicios
  - *Justificación de Prioridad:* Sirve como la interfaz de presentación de la trayectoria del staff de podólogos y catálogo de servicios (estrictamente sin precios visibles) que alimenta el inicio del flujo de navegación.
  - *Trazabilidad:* Responde al Punto 1 del Alcance Inicial del Product Brief.

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

- **Bloqueantes Potenciales:**
  - Dependencia crítica de la conectividad y entrega efectiva del servicio de WhatsApp para el despacho automático e inmediato (< 1 minuto) de confirmaciones y alertas.
  - Supuesto de que cada servicio podológico posee una duración estándar prefijada que permite calcular correctamente el bloque de tiempo acumulado.

- **Ambigüedades de Negocio:**
  - *Mecanismo de Autenticación de Clientes:* No está especificado si la gestión/cancelación por parte del cliente requiere creación de usuario/contraseña o se gestiona mediante un enlace seguro/código enviado a WhatsApp.
  - *Criterio de Asignación por Defecto de Podólogo:* Falta definir la regla de negocio para asignar podólogo cuando el cliente no selecciona uno de preferencia (ej. asignación por primer disponible o rotación equitativa).
  - *Ventana Límite para Cancelaciones:* No se han definido restricciones de tiempo mínimo previo a la cita (ej. X horas antes) para permitir cancelaciones autónomas.
  - *Política de Reagendamiento:* Falta aclarar si se permitirá reprogramar fecha/hora o si el cliente debe anular y crear una reserva nueva.

## 4. ORDEN DE DELEGACIÓN PARA EL BA

@BA: El análisis estratégico está completo en el archivo mvp_amely_spa.md. Tu primera asignación es leer ese documento y desglosar la Épica de Prioridad 1: Motor Inteligente de Reservas y Agenda Dinámica. Por favor, redacta la Historia de Usuario atómica, el Scope y los Criterios de Aceptación (Gherkin). ADVERTENCIA: Al redactar, ten presente esta restricción/ambigüedad detectada en el PRD: Definir cómo se manejará la asignación por defecto del podólogo cuando el usuario no seleccione uno explícitamente y cómo se validará en tiempo real el bloque continuo acumulado sin mostrar precios. Decláralo en tu output, no lo inventes. Procederé a revisar tu entregable una vez pase por QA Documental.
