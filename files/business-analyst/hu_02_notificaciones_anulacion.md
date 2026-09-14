# ESPECIFICACIÓN DE HISTORIA DE USUARIO

## 1. HISTORIA DE USUARIO

- **Épica:** Sistema de Notificaciones Instantáneas y Anulación por WhatsApp
- **Título de la HU:** Notificaciones Automáticas de Reserva y Anulación de Citas por WhatsApp

> **Como** Cliente del Spá Podológico Ámely  
> **Quiero** recibir una notificación inmediata por WhatsApp al agendar y contar con la opción de anular mi cita de forma sencilla  
> **Para** tener confirmación clara de mi reserva y permitir la liberación automática del horario en la agenda del podólogo en caso de no poder asistir.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Envío automático e instantáneo de mensaje de confirmación de reserva al WhatsApp del cliente y al WhatsApp del podólogo asignado tras completar el agendamiento.
  - Provisión de un mecanismo de anulación directa de la cita agendada por parte del cliente.
  - Actualización inmediata del estado de la cita a "Anulada" y liberación del bloque horario correspondiente en la agenda del podólogo.
  - Envío automático de notificación de cancelación al WhatsApp del podólogo informando sobre la liberación de su agenda.
  - Notificación de confirmación de anulación exitosa enviada al cliente.

- **NO Incluye:**
  - El proceso inicial de selección de servicios, podólogo y disponibilidad de horario (pertenece a la Épica P1: Motor de Reservas Inteligente).
  - Reprogramación automática de citas (requiere un nuevo flujo de agendamiento o alcance futuro).
  - Configuración o personalización dinámica de plantillas de mensaje desde un panel administrativo (pertenece a iteraciones posteriores).
  - Gestión manual del estado de la cita por parte del podólogo (pertenece a la Épica P3: Panel de Gestión de Citas para Profesionales).

## 3. REGLAS DE NEGOCIO

- **RN-01 (Despacho Instantáneo):** El envío de la notificación de confirmación debe detonarse de manera inmediata una vez que la reserva queda registrada exitosamente en el sistema.
- **RN-02 (Notificación Dual):** Cada evento relevante (reserva exitosa o anulación) debe notificar tanto al cliente como al podólogo asignado.
- **RN-03 (Liberación Inmediata de Agenda):** Al procesar una anulación por parte del cliente, el bloque horario asociado en la agenda del podólogo debe quedar disponible al instante para futuras reservas.
- **RN-04 (Irreversibilidad de Anulación):** Una vez confirmada la anulación de una cita, el registro cambia a estado final "Anulada" y no puede reactivarse.
- **RN-05 (Ocultación de Tarifas en Mensajes):** Las notificaciones de WhatsApp no deben incluir precios ni costos de los servicios atendiendo a la Restricción Comercial.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de notificaciones tras la confirmación de reserva (Happy Path)**
- **Dado** que el cliente ha completado exitosamente la reserva de una cita con un podólogo
- **Cuando** el sistema registra el agendamiento
- **Entonces** envía automáticamente un mensaje de confirmación al WhatsApp del cliente con el detalle de la fecha, hora y podólogo asignado
- **Y** envía una notificación en paralelo al WhatsApp del podólogo con los datos de la cita agendada.

**Escenario 2: Anulación exitosa de cita por parte del cliente y liberación de agenda (Happy Path)**
- **Dado** que el cliente cuenta con una cita en estado "Confirmada"
- **Cuando** el cliente ejecuta la acción de anular la cita
- **Entonces** el sistema cambia el estado de la cita a "Anulada" y libera de inmediato el bloque horario en la agenda del podólogo
- **Y** envía una notificación de cancelación al WhatsApp del podólogo indicando el horario liberado
- **Y** envía un mensaje de confirmación de anulación al WhatsApp del cliente.

**Escenario 3: Intento de anulación de una cita previamente anulada (Sad Path)**
- **Dado** que una cita ya se encuentra registrada con el estado "Anulada"
- **Cuando** el cliente intenta acceder o ejecutar nuevamente la anulación sobre dicha cita
- **Entonces** el sistema notifica que la cita ya fue cancelada previamente
- **Y** no genera nuevas notificaciones ni modificaciones en la agenda del podólogo.

**Escenario 4: Fallo de entrega en la API de WhatsApp (Sad Path)**
- **Dado** que el servicio de mensajería de WhatsApp presenta una interrupción temporal o error de conexión
- **Cuando** el sistema intenta despachar la notificación de confirmación o anulación
- **Entonces** el sistema registra el fallo de envío en log sin revertir la transacción de reserva o anulación en la base de datos
- **Y** muestra un aviso en pantalla informando que la acción se completó pero la notificación no pudo enviarse.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Mecanismo y Modelo de Acceso para Anulación):** No se especifica en el PRD si el cliente realizará la anulación mediante un enlace/token único enviado directamente a su WhatsApp o si requerirá autenticarse en una cuenta de usuario.
- **PA-02 (Ventana Límite de Anulación):** El PRD no especifica el tiempo mínimo de anticipación requerido para permitir la anulación sin penalización (ej. hasta 2 o 4 horas antes de la cita).
- **PA-03 (Estructura y Plantillas de Mensaje):** Falta definir el texto estándar exacto y los campos dinámicos que compondrán las plantillas de mensaje para confirmación y anulación vía WhatsApp.
- **DEP-01 (Proveedor de API de WhatsApp):** Dependencia técnica crítica de la integración con el servicio/proveedor de API de WhatsApp (ej. Twilio, Meta Business API) para el envío de mensajes salientes.
